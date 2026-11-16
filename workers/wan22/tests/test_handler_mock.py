"""
Testes sem GPU e sem torch: o motor do Wan 2.2 é substituído por um falso que devolve
frames sintéticos (uma cor sólida por plano). Cobrem o contrato (igual ao do worker
HoloCine), a matemática de planos/cortes/4k+1, seeds por plano, defaults oficiais de cada
variante, codificação MP4 real com cortes secos nos frames certos, limite de 10 MB do
/run, upload presigned, escolha de modo de memória, checagem do volume e o conversor
F32 -> BF16 com módulos mantidos em F32.

Rodar (de dentro da pasta do worker):
  python -m pytest -q tests      (ou: python -m unittest discover -s tests -v)
Requer: numpy, imageio==2.37.0, imageio-ffmpeg==0.6.0 (torch é opcional).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.dirname(HERE)
sys.path.insert(0, WORKER)

import handler  # noqa: E402
import convert_to_bf16  # noqa: E402

A14B = handler.VARIANTS["a14b"]
TI2V = handler.VARIANTS["ti2v-5b"]
SHOT_COLORS = [(230, 20, 20), (20, 200, 30), (30, 40, 220), (220, 200, 20), (200, 30, 200)]


def job(inp, job_id="test-job"):
    return {"id": job_id, "input": inp}


def base_input(**overrides):
    inp = {
        "global_caption": "[character1] is a lighthouse keeper with a gray beard and a red wool cap. "
                          "A rocky coast at dusk, cold blue palette. This scene contains 2 shots.",
        "shot_captions": [
            "Wide shot of the lighthouse on the cliff, waves crashing below.",
            "Close-up of [character1] lighting a lantern, warm glow on his face.",
        ],
        "num_frames": 81,
        "shot_cut_frames": [],
        "seed": 42,
        "output_path": "cenas/teste_01.mp4",
    }
    inp.update(overrides)
    return inp


class FakeEngine:
    """Imita WanEngine: encode() uma vez por job, generate() uma vez por plano."""

    def __init__(self, vram_gb=85.0, device="cuda", noise=False, size=None, raise_exc=None,
                 short_by=0):
        self.encode_calls = []
        self.generate_calls = []
        self.flow_shifts = []
        self.tiling_calls = []
        self.vae_tiling = False
        self.device = device
        self.noise = noise
        self.size = size
        self.raise_exc = raise_exc
        self.short_by = short_by
        self.info = {"variant": handler.VARIANT, "gpu": "FakeGPU", "vram_gb": vram_gb,
                     "offload": "t5", "revision": handler.SPEC["revision"]}

    def encode(self, prompts, negative):
        self.encode_calls.append((list(prompts), negative))
        return {"pos": list(prompts), "neg": negative}

    def set_flow_shift(self, shift):
        self.flow_shifts.append(shift)

    def set_vae_tiling(self, enabled):
        self.tiling_calls.append(enabled)
        self.vae_tiling = enabled

    def generate(self, embeds, index, *, height, width, num_frames, steps, cfg_scale, cfg_scale_2,
                 seed, on_step=None):
        self.generate_calls.append(dict(prompt=embeds["pos"][index], negative=embeds["neg"], index=index,
                                        height=height, width=width, num_frames=num_frames, steps=steps,
                                        cfg_scale=cfg_scale, cfg_scale_2=cfg_scale_2, seed=seed))
        if self.raise_exc:
            raise self.raise_exc
        for s in range(1, steps + 1):
            if on_step:
                on_step(s, steps)
        h, w = self.size or (64, 96)
        n = num_frames - self.short_by
        if self.noise:
            rng = np.random.default_rng(seed)
            return rng.integers(0, 256, size=(n, h, w, 3), dtype=np.uint8)
        frames = np.zeros((n, h, w, 3), dtype=np.uint8)
        frames[:] = SHOT_COLORS[index % len(SHOT_COLORS)]
        return frames


class WordTokenizer:
    def __call__(self, text, add_special_tokens=True):
        return {"input_ids": text.split() + (["</s>"] if add_special_tokens else [])}


def read_mp4_frames(data: bytes):
    import imageio  # noqa: WPS433

    path = os.path.join(tempfile.mkdtemp(prefix="mp4-"), "v.mp4")
    with open(path, "wb") as fh:
        fh.write(data)
    reader = imageio.get_reader(path, format="FFMPEG")
    try:
        return [np.asarray(f) for f in reader]
    finally:
        reader.close()


class HandlerTestBase(unittest.TestCase):
    spec = A14B

    def setUp(self):
        self._orig = (handler.PIPELINE_FACTORY, handler.TOKENIZER_FACTORY, handler.MAX_INLINE_B64,
                      handler.SAVE_OUTPUTS, handler.OUTPUT_DIR, handler.SPEC, handler.VARIANT,
                      handler.VAE_TILING, handler.VRAM_PROBE)
        handler.VRAM_PROBE = lambda: 0.0
        handler.SPEC = self.spec
        handler.VARIANT = "a14b" if self.spec is A14B else "ti2v-5b"
        handler._ENGINE = None
        handler._TOKENIZER = None
        handler._TOKENIZER_FAILED = False
        self.engine = FakeEngine()
        handler.PIPELINE_FACTORY = lambda: self.engine
        handler.TOKENIZER_FACTORY = lambda: WordTokenizer()

    def tearDown(self):
        (handler.PIPELINE_FACTORY, handler.TOKENIZER_FACTORY, handler.MAX_INLINE_B64,
         handler.SAVE_OUTPUTS, handler.OUTPUT_DIR, handler.SPEC, handler.VARIANT,
         handler.VAE_TILING, handler.VRAM_PROBE) = self._orig
        handler._ENGINE = None


class TestFrameMath(unittest.TestCase):
    def test_enforce_4t_plus_1_matches_holocine_contract(self):
        for n in (81, 121, 161, 241, 321, 401, 481):
            self.assertEqual(handler.enforce_4t_plus_1(n), n)
        self.assertEqual(handler.enforce_4t_plus_1(240), 241)
        self.assertEqual(handler.enforce_4t_plus_1(100), 101)

    def test_snap_up_is_smallest_4k_plus_1_not_below(self):
        self.assertEqual([handler.snap_up_4k1(n) for n in (1, 2, 5, 8, 9, 40, 41, 42, 80, 81)],
                         [1, 5, 5, 9, 9, 41, 41, 45, 81, 81])
        for n in range(1, 200):
            s = handler.snap_up_4k1(n)
            self.assertGreaterEqual(s, n)
            self.assertEqual((s - 1) % 4, 0)
            self.assertLess(s - n, 4)

    def test_auto_cuts_and_segments(self):
        self.assertEqual(handler.auto_shot_cuts(241, 5), [49, 97, 145, 193])
        self.assertEqual(handler.auto_shot_cuts(81, 2), [41])
        self.assertEqual(handler.auto_shot_cuts(81, 1), [])
        self.assertEqual(handler.shot_segments(81, [41]), [(0, 41), (41, 40)])
        segs = handler.shot_segments(241, [49, 97, 145, 193])
        self.assertEqual(sum(length for _, length in segs), 241)

    def test_shot_seeds_are_deterministic_distinct_and_in_range(self):
        self.assertEqual(handler.derive_shot_seed(42, 0), 42)
        seeds = [handler.derive_shot_seed(42, i) for i in range(13)]
        self.assertEqual(len(set(seeds)), 13)
        self.assertEqual(seeds, [handler.derive_shot_seed(42, i) for i in range(13)])
        for s in seeds + [handler.derive_shot_seed(2**31 - 1, i) for i in range(13)]:
            self.assertTrue(1 <= s <= 2**31 - 1)


class TestPromptsAndDefaults(unittest.TestCase):
    def test_shot_prompt_is_global_plus_shot_without_scene_phrase(self):
        plan = handler.validate_and_build(base_input(), A14B)
        p0 = plan["shots"][0]["prompt"]
        self.assertTrue(p0.startswith("[character1] is a lighthouse keeper"))
        self.assertTrue(p0.endswith("Wide shot of the lighthouse on the cliff, waves crashing below."))
        self.assertNotIn("This scene contains", p0)
        self.assertNotIn("  ", p0)

    def test_raw_holocine_prompt_is_split_into_shots(self):
        plan = handler.validate_and_build({
            "prompt": "[global caption] A studio. This scene contains 3 shots. [per shot caption] "
                      "A. [shot cut] B. [shot cut] C.",
            "num_frames": 81, "shot_cut_frames": [29, 57]}, A14B)
        self.assertEqual(plan["num_shots"], 3)
        self.assertEqual(plan["shot_cut_frames"], [29, 57])
        self.assertEqual([s["prompt"] for s in plan["shots"]], ["A studio. A.", "A studio. B.", "A studio. C."])

    def test_official_defaults_a14b(self):
        plan = handler.validate_and_build({"global_caption": "A harbor at dawn.",
                                           "shot_captions": ["Wide shot."]}, A14B)
        self.assertEqual((plan["num_frames"], plan["height"], plan["width"], plan["fps"]), (81, 480, 832, 16))
        self.assertEqual((plan["num_inference_steps"], plan["cfg_scale"], plan["cfg_scale_2"]), (40, 4.0, 3.0))
        self.assertEqual(plan["flow_shift"], 12.0)
        self.assertEqual(plan["negative_prompt"], handler.DEFAULT_NEGATIVE_PROMPT)

    def test_official_defaults_ti2v_5b(self):
        plan = handler.validate_and_build({"global_caption": "A harbor at dawn.",
                                           "shot_captions": ["Wide shot."]}, TI2V)
        self.assertEqual((plan["num_frames"], plan["height"], plan["width"], plan["fps"]), (121, 704, 1280, 24))
        self.assertEqual((plan["num_inference_steps"], plan["cfg_scale"], plan["cfg_scale_2"]), (50, 5.0, None))
        self.assertEqual(plan["flow_shift"], 5.0)

    def test_env_overrides_flow_shift(self):
        with mock.patch.dict(os.environ, {"WAN_FLOW_SHIFT": "3.0"}):
            plan = handler.validate_and_build(base_input(), A14B)
        self.assertEqual(plan["flow_shift"], 3.0)

    def test_shot_plan_snaps_up_and_trims_back(self):
        plan = handler.validate_and_build(base_input(), A14B)
        self.assertEqual(plan["shot_cut_frames"], [41])
        self.assertEqual([(s["start_frame"], s["frames_used"], s["frames_generated"]) for s in plan["shots"]],
                         [(0, 41, 41), (41, 40, 41)])
        self.assertEqual(plan["shots"][0]["seed"], 42)
        self.assertNotEqual(plan["shots"][1]["seed"], 42)


class TestValidation(unittest.TestCase):
    def assertInvalid(self, inp, fragment, spec=A14B):
        with self.assertRaises(handler.InputError) as ctx:
            handler.validate_and_build(inp, spec)
        self.assertIn(fragment, str(ctx.exception))

    def test_rejections(self):
        self.assertInvalid(None, "objeto JSON")
        self.assertInvalid({}, "global_caption + shot_captions")
        self.assertInvalid(base_input(shot_captions=[]), "pelo menos 1 plano")
        self.assertInvalid(base_input(shot_captions=["x"] * 14, global_caption="A scene."), "máximo de 13")
        self.assertInvalid(base_input(shot_captions=["ok", 3]), "texto")
        self.assertInvalid(base_input(shot_captions=["a [shot cut] b", "c"]), "tag reservada")
        self.assertInvalid(base_input(shot_captions=["a", "b", "c"]), "diz 2 planos")
        self.assertInvalid(base_input(global_caption="This scene contains many shots."), "malformada")
        self.assertInvalid(base_input(shot_cut_frames=[41, 61]), "exigem 1")
        self.assertInvalid(base_input(shot_cut_frames=[200]), "fora do intervalo")
        self.assertInvalid(base_input(num_frames=2000), "num_frames")
        self.assertInvalid(base_input(num_frames="81"), "inteiro")
        self.assertInvalid(base_input(seed=-1), "seed")
        self.assertInvalid(base_input(height=500), "múltiplos de 16")
        self.assertInvalid(base_input(height=1088, width=1280), "limite")
        self.assertInvalid(base_input(flow_shift=50), "flow_shift")
        self.assertInvalid(base_input(cfg_scale_2=0.5), "cfg_scale_2")
        self.assertInvalid(base_input(output_path="../etc/passwd"), "output_path")
        self.assertInvalid(base_input(output_path="/abs/x.mp4"), "relativo")
        self.assertInvalid(base_input(output_upload_url="http://example.com/x"), "https")
        self.assertInvalid(base_input(output_upload_url="https://127.0.0.1/x"), "rede interna")
        self.assertInvalid(base_input(output_upload_url="https://10.1.2.3/x"), "rede interna")
        self.assertInvalid(base_input(output_upload_url="https://localhost/x"), "rede interna")
        self.assertInvalid(base_input(return_base64=False), "exige output_upload_url")
        self.assertInvalid(base_input(num_frames=17, global_caption="A scene.",
                                      shot_captions=[f"s{i}" for i in range(13)]), "pouco para 13")
        self.assertInvalid({"prompt": "[global caption] A. [per shot caption] B. [shot cut] "}, "vazio")

    def test_long_shot_rejected_before_gpu(self):
        # 241 frames em 2 planos -> 121 frames por plano > 81 do A14B
        self.assertInvalid(base_input(num_frames=241), "no máximo 81")
        plan = handler.validate_and_build(base_input(num_frames=241), TI2V)  # 5B aceita 121
        self.assertEqual([s["frames_generated"] for s in plan["shots"]], [121, 121])

    def test_total_runtime_budget_rejects_before_gpu(self):
        # 481 frames em 6 planos de 81 no A14B ≈ 6 × 786 s ≈ 4700 s > 3000 s (timeout 3600 s)
        cuts = [81, 161, 241, 321, 401]
        self.assertInvalid(base_input(num_frames=481, global_caption="A harbor.",
                                      shot_captions=[f"Shot {i}." for i in range(6)],
                                      shot_cut_frames=cuts), "min de GPU")
        ok = handler.validate_and_build(base_input(height=720, width=1280), A14B)  # 720P 81 frames cabe
        self.assertLess(ok["estimated_gen_s"], A14B["max_gen_seconds"])
        with mock.patch.dict(os.environ, {"WAN_MAX_GEN_SECONDS": "100"}):
            self.assertInvalid(base_input(), "min de GPU")
        with mock.patch.dict(os.environ, {"WAN_REF_SECONDS": "100"}):  # GPU medida mais rápida
            plan = handler.validate_and_build(base_input(num_frames=481, global_caption="A harbor.",
                                                         shot_captions=[f"Shot {i}." for i in range(6)],
                                                         shot_cut_frames=cuts), A14B)
            self.assertEqual(plan["num_shots"], 6)
        # 5B: 241 frames em 2 planos de 121 ≈ 1200 s cabe em 1500 s; 481 frames em 4 planos não
        self.assertLess(handler.validate_and_build(base_input(num_frames=241), TI2V)["estimated_gen_s"], 1500)
        self.assertInvalid(base_input(num_frames=481, global_caption="A harbor.",
                                      shot_captions=[f"Shot {i}." for i in range(4)]), "min de GPU", TI2V)

    def test_cfg2_without_cfg1_is_rejected(self):
        self.assertInvalid(base_input(cfg_scale=1.0, cfg_scale_2=3.0), "cfg_scale=1 desliga")
        handler.validate_and_build(base_input(cfg_scale=1.0, cfg_scale_2=1.0), A14B)
        handler.validate_and_build(base_input(cfg_scale=4.0, cfg_scale_2=1.0), A14B)

    def test_tiny_shot_rejected(self):
        self.assertInvalid(base_input(num_frames=81, shot_cut_frames=[5]), "< 8")

    def test_ti2v_needs_multiple_of_32_and_ignores_cfg2(self):
        self.assertInvalid(base_input(height=720, width=1280), "múltiplos de 32", TI2V)
        plan = handler.validate_and_build(base_input(height=704, width=1280, cfg_scale_2=3.0,
                                                     num_frames=121), TI2V)
        self.assertIsNone(plan["cfg_scale_2"])
        self.assertTrue(any("cfg_scale_2 ignorado" in w for w in plan["warnings"]))

    def test_unofficial_size_warns(self):
        plan = handler.validate_and_build(base_input(height=512, width=512), A14B)
        self.assertTrue(any("fora das oficiais" in w for w in plan["warnings"]))
        plan = handler.validate_and_build(base_input(height=720, width=1280), A14B)
        self.assertFalse(any("fora das oficiais" in w for w in plan["warnings"]))

    def test_unknown_keys_only_warn_and_frames_corrected(self):
        plan = handler.validate_and_build(base_input(foo=1, num_frames=80), A14B)
        self.assertTrue(any("foo" in w for w in plan["warnings"]))
        self.assertEqual(plan["num_frames"], 81)

    def test_seed_zero_is_random_and_fixed_seed_kept(self):
        a = handler.validate_and_build(base_input(seed=0), A14B)["seed"]
        b = handler.validate_and_build(base_input(seed=0), A14B)["seed"]
        self.assertGreater(a, 0)
        self.assertNotEqual(a, b)
        self.assertEqual(handler.validate_and_build(base_input(seed=777), A14B)["seed"], 777)

    def test_portuguese_captions_warn_chinese_does_not(self):
        pt = handler.validate_and_build(base_input(global_caption="Ação à noite, coração, ônibus, maçã.",
                                                   shot_captions=["Plano geral.", "Close."]), A14B)
        self.assertTrue(any("inglês" in w for w in pt["warnings"]))
        zh = handler.validate_and_build(base_input(global_caption="夜晚的海港，灯塔亮着。",
                                                   shot_captions=["远景。", "特写。"]), A14B)
        self.assertFalse(any("inglês" in w for w in zh["warnings"]))


class TestHandler(HandlerTestBase):
    def test_end_to_end_inline_base64_with_hard_cut_at_requested_frame(self):
        out = handler.handler(job(base_input()))
        self.assertNotIn("error", out, out.get("error"))
        mp4 = base64.b64decode(out["video_b64"])
        self.assertIn(b"ftyp", mp4[:64])
        self.assertEqual(out["frames"], 81)
        self.assertEqual(out["fps"], 16)
        self.assertAlmostEqual(out["seconds"], 5.06)
        self.assertEqual(out["seed"], 42)
        self.assertEqual(out["file_name"], "teste_01.mp4")
        self.assertEqual(out["size_bytes"], len(mp4))
        self.assertEqual(out["sha256"], hashlib.sha256(mp4).hexdigest())
        self.assertEqual(out["shot_cut_frames"], [41])
        self.assertEqual([s["frames_used"] for s in out["shots"]], [41, 40])
        self.assertTrue(out["prompt_tokens_exact"])
        # um encode por job com todos os prompts; um generate por plano
        self.assertEqual(len(self.engine.encode_calls), 1)
        prompts, negative = self.engine.encode_calls[0]
        self.assertEqual(len(prompts), 2)
        self.assertEqual(negative, handler.DEFAULT_NEGATIVE_PROMPT)
        calls = self.engine.generate_calls
        self.assertEqual([c["num_frames"] for c in calls], [41, 41])
        self.assertEqual([c["seed"] for c in calls], [42, handler.derive_shot_seed(42, 1)])
        self.assertEqual((calls[0]["cfg_scale"], calls[0]["cfg_scale_2"], calls[0]["steps"]), (4.0, 3.0, 40))
        self.assertEqual((calls[0]["height"], calls[0]["width"]), (480, 832))
        self.assertEqual(self.engine.flow_shifts, [12.0])
        # o MP4 tem exatamente 81 frames e o corte seco cai no frame 41
        decoded = read_mp4_frames(mp4)
        self.assertEqual(len(decoded), 81)
        means = [f.reshape(-1, 3).mean(axis=0) for f in decoded]
        self.assertGreater(means[40][0], 150)   # último frame do plano 1: vermelho
        self.assertGreater(means[41][1], 150)   # primeiro frame do plano 2: verde
        self.assertLess(means[41][0], 100)

    def test_single_shot_uses_whole_clip(self):
        out = handler.handler(job(base_input(global_caption="A desert road.",
                                             shot_captions=["Wide static shot of the road."])))
        self.assertNotIn("error", out)
        self.assertEqual(out["shot_cut_frames"], [])
        self.assertEqual([c["num_frames"] for c in self.engine.generate_calls], [81])

    def test_engine_loaded_once_per_worker(self):
        calls = []

        def factory():
            calls.append(1)
            return self.engine

        handler.PIPELINE_FACTORY = factory
        first = handler.handler(job(base_input()))
        second = handler.handler(job(base_input()))
        self.assertEqual(len(calls), 1)
        self.assertGreaterEqual(first["model_load_s"], 0.0)
        self.assertEqual(second["model_load_s"], 0.0)

    def test_crf_escalates_to_fit_inline_limit(self):
        self.engine = FakeEngine(noise=True)
        probe = self.engine.generate({"pos": ["p"], "neg": None}, 0, height=64, width=96, num_frames=81,
                                     steps=1, cfg_scale=4.0, cfg_scale_2=3.0, seed=1)
        first = handler.ENCODER(probe, 16, 23, os.path.join(tempfile.mkdtemp(), "probe.mp4"))
        handler.MAX_INLINE_B64 = int(handler.b64_len(first) * 0.8)
        self.engine.generate_calls.clear()
        out = handler.handler(job(base_input()))
        if "error" in out:
            self.assertIn("10 MB", out["error"])
        else:
            self.assertGreater(out["crf"], 23)
            self.assertLessEqual(len(out["video_b64"]), handler.MAX_INLINE_B64)

    def test_too_big_even_after_ladder_returns_error(self):
        self.engine = FakeEngine(noise=True)
        handler.MAX_INLINE_B64 = 1000
        out = handler.handler(job(base_input()))
        self.assertIn("error", out)
        self.assertIn("output_upload_url", out["error"])

    def test_presigned_upload_without_base64(self):
        captured = {}

        class Resp:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=0):
            captured["method"] = req.get_method()
            captured["ct"] = req.get_header("Content-type")
            captured["len"] = len(req.data)
            captured["url"] = req.full_url
            return Resp()

        url = "https://bucket.s3.amazonaws.com/cenas/x.mp4?X-Amz-Signature=abc"
        with mock.patch.object(handler.urllib.request, "urlopen", fake_urlopen):
            out = handler.handler(job(base_input(output_upload_url=url, return_base64=False)))
        self.assertNotIn("error", out)
        self.assertTrue(out["uploaded"])
        self.assertNotIn("video_b64", out)
        self.assertEqual(captured["method"], "PUT")
        self.assertEqual(captured["ct"], "video/mp4")
        self.assertEqual(captured["len"], out["size_bytes"])
        self.assertEqual(captured["url"], url)

    def test_save_copy_to_volume_when_enabled(self):
        handler.SAVE_OUTPUTS = True
        handler.OUTPUT_DIR = tempfile.mkdtemp(prefix="vol-")
        out = handler.handler(job(base_input()))
        dest = os.path.join(handler.OUTPUT_DIR, "cenas", "teste_01.mp4")
        self.assertTrue(os.path.isfile(dest))
        self.assertEqual(out["volume_path"], dest)

    def test_prompt_over_512_tokens_per_shot_rejected_before_gpu(self):
        long_global = " ".join(["word"] * 480)      # 2399 caracteres, abaixo do limite de 4000
        long_shot = " ".join(["detail"] * 100)      # 699 caracteres, abaixo do limite de 1200
        # plano 1: 480 + 2 + </s> = 483 tokens (ok); plano 2: 480 + 100 + </s> = 581 (> 512)
        out = handler.handler(job(base_input(global_caption=long_global,
                                             shot_captions=["Short shot.", long_shot])))
        self.assertIn("error", out)
        self.assertIn("plano 2", out["error"])
        self.assertEqual(self.engine.generate_calls, [])
        self.assertIsNone(handler._ENGINE)  # nem carregou o modelo
        ok = handler.handler(job(base_input(global_caption=long_global,
                                            shot_captions=["Short shot.", long_shot],
                                            allow_prompt_truncation=True)))
        self.assertNotIn("error", ok)
        self.assertTrue(any("tokens" in w for w in ok["warnings"]))

    def test_invalid_input_never_touches_engine(self):
        out = handler.handler(job({"shot_captions": ["x"]}))
        self.assertTrue(out["error"].startswith("entrada inválida"))
        self.assertIsNone(handler._ENGINE)

    def test_engine_exceptions_become_errors(self):
        class OutOfMemoryError(RuntimeError):
            pass

        self.engine = FakeEngine(raise_exc=OutOfMemoryError("CUDA out of memory"))
        out = handler.handler(job(base_input()))
        self.assertIn("480x832", out["error"])
        handler._ENGINE = None
        self.engine = FakeEngine(raise_exc=RuntimeError("CUDA error: device-side assert triggered"))
        out = handler.handler(job(base_input()))
        self.assertTrue(out.get("refresh_worker"))

    def test_short_output_from_engine_is_an_error(self):
        self.engine = FakeEngine(short_by=8)
        out = handler.handler(job(base_input()))
        self.assertIn("error", out)
        self.assertIn("frames", out["error"])

    def test_720p_on_48gb_is_refused_for_a14b_before_loading(self):
        handler.VRAM_PROBE = lambda: 51.5   # A40/A6000: 48 GiB = ~51,5 GB decimais
        loads = []
        handler.PIPELINE_FACTORY = lambda: loads.append(1) or self.engine
        out = handler.handler(job(base_input(height=720, width=1280)))
        self.assertIn("80 GB", out["error"])
        self.assertEqual(loads, [])          # o modelo nem foi carregado
        self.assertIsNone(handler._ENGINE)
        handler.VRAM_PROBE = lambda: 85.0
        self.assertNotIn("error", handler.handler(job(base_input(height=720, width=1280))))

    def test_vae_tiling_policy(self):
        self.engine = FakeEngine(vram_gb=85.0)
        handler.handler(job(base_input()))                          # 480P em 80 GB
        handler._ENGINE = None
        handler.handler(job(base_input(height=720, width=1280)))    # 720P liga tiling
        self.assertEqual(self.engine.tiling_calls, [False, True])
        handler.VAE_TILING = "0"
        handler._ENGINE = None
        handler.handler(job(base_input(height=720, width=1280)))
        self.assertEqual(self.engine.tiling_calls[-1], False)

    def test_crf_ladder_has_at_most_two_extra_encodes(self):
        self.assertEqual(handler.crf_ladder(23), [23, 27, 31])
        self.assertEqual(handler.crf_ladder(36), [36, 40])
        self.engine = FakeEngine(noise=True)
        handler.MAX_INLINE_B64 = 1000
        encodes = []
        orig = handler.ENCODER
        handler.ENCODER = lambda *a: encodes.append(1) or orig(*a)
        try:
            out = handler.handler(job(base_input()))
        finally:
            handler.ENCODER = orig
        self.assertIn("error", out)
        self.assertEqual(len(encodes), 3)

    def test_failed_upload_does_not_sleep_after_last_attempt(self):
        sleeps = []

        def boom(req, timeout=0):
            raise OSError("rede caiu")

        with mock.patch.object(handler.urllib.request, "urlopen", boom), \
                mock.patch.object(handler.time, "sleep", sleeps.append):
            with self.assertRaises(RuntimeError):
                handler.http_put("https://bucket.example.com/x", b"abc", "video/mp4", attempts=3)
        self.assertEqual(sleeps, [1, 2])

    def test_cfg_one_skips_negative_encoding(self):
        out = handler.handler(job(base_input(cfg_scale=1.0, cfg_scale_2=1.0)))
        self.assertNotIn("error", out)
        self.assertIsNone(self.engine.encode_calls[0][1])


class TestHandlerTi2v(HandlerTestBase):
    spec = TI2V

    def test_ti2v_defaults_flow_through_and_no_second_guidance(self):
        self.engine = FakeEngine(vram_gb=51.5)  # A40 reporta 48 GiB = ~51,5 GB decimais
        out = handler.handler(job(base_input(num_frames=121)))
        self.assertNotIn("error", out, out.get("error"))
        self.assertEqual((out["frames"], out["fps"], out["width"], out["height"]), (121, 24, 1280, 704))
        calls = self.engine.generate_calls
        self.assertEqual([c["num_frames"] for c in calls], [61, 61])
        self.assertTrue(all(c["cfg_scale_2"] is None for c in calls))
        self.assertEqual(self.engine.flow_shifts, [5.0])
        self.assertEqual(self.engine.tiling_calls, [True])  # GPU de 48 GB: VAE em tiles


class TestOffloadAndVolume(unittest.TestCase):
    def test_choose_offload_table(self):
        c = handler.choose_offload
        self.assertEqual(c("a14b", 85.0, "auto", "cuda"), "t5")
        self.assertEqual(c("a14b", 47.7, "auto", "cuda"), "model")
        self.assertEqual(c("ti2v-5b", 47.7, "auto", "cuda"), "none")
        self.assertEqual(c("ti2v-5b", 32.0, "auto", "cuda"), "t5")
        self.assertEqual(c("ti2v-5b", 25.4, "auto", "cuda"), "model")
        self.assertEqual(c("a14b", 0.0, "auto", "cpu"), "none")
        with self.assertRaises(RuntimeError):
            c("a14b", 25.4, "auto", "cuda")
        with self.assertRaises(RuntimeError):
            c("ti2v-5b", 16.0, "auto", "cuda")
        with self.assertRaises(RuntimeError):
            c("a14b", 47.7, "t5", "cuda")
        with self.assertRaises(RuntimeError):
            c("a14b", 85.0, "turbo", "cuda")

    def _make_layout(self, root, variant, drop=()):
        spec = handler.VARIANTS[variant]
        path = os.path.join(root, spec["dir"])
        files = ["model_index.json", "scheduler/scheduler_config.json", "tokenizer/tokenizer.json",
                 "tokenizer/tokenizer_config.json", "text_encoder/config.json",
                 "vae/config.json", "vae/diffusion_pytorch_model.safetensors"]
        comps = ["transformer", "transformer_2"] if spec["two_experts"] else ["transformer"]
        for comp in comps:
            files.append(f"{comp}/config.json")
        for rel in files:
            os.makedirs(os.path.dirname(os.path.join(path, rel)), exist_ok=True)
            open(os.path.join(path, rel), "w").close()
        for comp, shards in [("text_encoder", ["model-00001-of-00002.safetensors",
                                               "model-00002-of-00002.safetensors"])] + \
                [(c, ["diffusion_pytorch_model-00001-of-00002.safetensors",
                      "diffusion_pytorch_model-00002-of-00002.safetensors"]) for c in comps]:
            idx_name = "model.safetensors.index.json" if comp == "text_encoder" \
                else "diffusion_pytorch_model.safetensors.index.json"
            with open(os.path.join(path, comp, idx_name), "w") as fh:
                json.dump({"metadata": {"total_size": 1}, "weight_map": {f"w{i}": s for i, s in enumerate(shards)}}, fh)
            for s in shards:
                if f"{comp}/{s}" not in drop:
                    open(os.path.join(path, comp, s), "w").close()
        return path

    def test_complete_layout_passes_and_missing_shards_are_listed(self):
        root = tempfile.mkdtemp()
        self._make_layout(root, "a14b")
        self.assertTrue(handler.resolve_model_dir(root, "a14b").endswith("Wan2.2-T2V-A14B-Diffusers"))
        root2 = tempfile.mkdtemp()
        self._make_layout(root2, "a14b", drop=("transformer_2/diffusion_pytorch_model-00002-of-00002.safetensors",))
        with self.assertRaises(RuntimeError) as ctx:
            handler.resolve_model_dir(root2, "a14b")
        self.assertIn("transformer_2/diffusion_pytorch_model-00002-of-00002.safetensors", str(ctx.exception))
        with self.assertRaises(RuntimeError) as ctx:
            handler.resolve_model_dir(tempfile.mkdtemp(), "ti2v-5b")
        self.assertIn("VARIANT=ti2v-5b", str(ctx.exception))

    def test_ti2v_layout_does_not_need_transformer_2(self):
        root = tempfile.mkdtemp()
        self._make_layout(root, "ti2v-5b")
        self.assertTrue(handler.resolve_model_dir(root, "ti2v-5b").endswith("Wan2.2-TI2V-5B-Diffusers"))

    def test_ready_marker(self):
        root = tempfile.mkdtemp()
        path = self._make_layout(root, "a14b")
        self.assertFalse(handler.ready_marker_ok(path, "a14b"))
        with open(os.path.join(path, ".cineforge_ready"), "w") as fh:
            fh.write(f"revision={A14B['revision']}\n")
        self.assertTrue(handler.ready_marker_ok(path, "a14b"))


def _write_safetensors(path, tensors, metadata=None):
    header, blobs, off = {}, [], 0
    for name, arr in tensors.items():
        data = np.ascontiguousarray(arr, dtype="<f4").tobytes()
        header[name] = {"dtype": "F32", "shape": list(arr.shape), "data_offsets": [off, off + len(data)]}
        blobs.append(data)
        off += len(data)
    if metadata:
        header["__metadata__"] = metadata
    raw = json.dumps(header).encode()
    raw += b" " * ((8 - len(raw) % 8) % 8)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<Q", len(raw)) + raw + b"".join(blobs))


def _read_safetensors(path):
    with open(path, "rb") as fh:
        (n,) = struct.unpack("<Q", fh.read(8))
        header = json.loads(fh.read(n))
        body = fh.read()
    out = {}
    for k, v in header.items():
        if k == "__metadata__":
            continue
        b, e = v["data_offsets"]
        out[k] = (v["dtype"], v["shape"], body[b:e])
    return header, out


class TestConvertToBf16(unittest.TestCase):
    KEEP = "time_embedder,scale_shift_table,norm1,norm2,norm3"

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="conv-")
        rng = np.random.default_rng(123)
        self.tensors = {
            "blocks.0.attn1.to_q.weight": rng.standard_normal((64, 48)).astype("<f4"),
            "blocks.0.norm2.weight": rng.standard_normal(48).astype("<f4"),
            "blocks.0.scale_shift_table": rng.standard_normal((1, 6, 48)).astype("<f4"),
            "condition_embedder.time_embedder.linear_1.weight": rng.standard_normal((48, 16)).astype("<f4"),
            "proj_out.bias": rng.standard_normal(16).astype("<f4") * 1e-3,
            "specials": np.array([1.0, -0.0, np.inf, np.nan, 1.00390625,
                                  np.frombuffer(struct.pack("<I", 0x3F818000), "<f4")[0]], dtype="<f4"),
        }
        self.src = os.path.join(self.dir, "diffusion_pytorch_model-00001-of-00001.safetensors")
        _write_safetensors(self.src, self.tensors, {"format": "pt"})

    def test_hand_checked_rounding(self):
        out = np.frombuffer(convert_to_bf16.f32_to_bf16(np.array(
            [1.0, 1.00390625, np.frombuffer(struct.pack("<I", 0x3F818000), "<f4")[0],
             np.inf, np.nan, np.float32(3.4028235e38)], dtype="<f4").tobytes()), "<u2")
        self.assertEqual([hex(x) for x in out], ["0x3f80", "0x3f80", "0x3f82", "0x7f80", "0x7fc0", "0x7f80"])

    def test_keep_fp32_modules_stay_bit_identical(self):
        dst = os.path.join(self.dir, "out", "diffusion_pytorch_model-00001-of-00001.safetensors")
        with open(self.src, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        rc = convert_to_bf16.main(["--src", self.src, "--dst", dst, "--expect-sha256", sha,
                                   "--keep-fp32", self.KEEP])
        self.assertEqual(rc, 0)
        header, out = _read_safetensors(dst)
        self.assertEqual(set(out), set(self.tensors))
        self.assertEqual(header["__metadata__"]["format"], "pt")
        kept = {"blocks.0.norm2.weight", "blocks.0.scale_shift_table",
                "condition_embedder.time_embedder.linear_1.weight"}
        for name, arr in self.tensors.items():
            dtype, shape, raw = out[name]
            self.assertEqual(shape, list(arr.shape))
            if name in kept:
                self.assertEqual(dtype, "F32", name)
                self.assertEqual(raw, np.ascontiguousarray(arr, "<f4").tobytes(), name)
            else:
                self.assertEqual(dtype, "BF16", name)
                self.assertEqual(raw, convert_to_bf16.f32_to_bf16(np.ascontiguousarray(arr, "<f4").tobytes()))
        # sem --keep-fp32 tudo vira BF16
        dst2 = os.path.join(self.dir, "all.safetensors")
        convert_to_bf16.main(["--src", self.src, "--dst", dst2])
        _, out2 = _read_safetensors(dst2)
        self.assertTrue(all(v[0] == "BF16" for v in out2.values()))

    def test_matches_torch_when_available(self):
        try:
            import torch
            from safetensors.torch import load_file
        except ImportError:
            self.skipTest("torch ausente: comparação bit a bit pulada")
        dst = os.path.join(self.dir, "t.safetensors")
        convert_to_bf16.main(["--src", self.src, "--dst", dst, "--keep-fp32", self.KEEP])
        loaded = load_file(dst)
        for name, arr in self.tensors.items():
            ref = torch.from_numpy(np.array(arr))
            if loaded[name].dtype == torch.float32:
                self.assertTrue(torch.equal(loaded[name], ref) or torch.isnan(ref).any())
                continue
            ref = ref.to(torch.bfloat16)
            self.assertTrue(torch.equal(torch.nan_to_num(loaded[name].float(), nan=7.0),
                                        torch.nan_to_num(ref.float(), nan=7.0)), name)

    def test_stdin_stream_and_bad_sha(self):
        dst = os.path.join(self.dir, "s.safetensors")
        with open(self.src, "rb") as fh:
            res = subprocess.run([sys.executable, os.path.join(WORKER, "convert_to_bf16.py"),
                                  "--src", "-", "--dst", dst, "--keep-fp32", self.KEEP],
                                 stdin=fh, capture_output=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertTrue(os.path.isfile(dst + ".sha256"))
        bad = os.path.join(self.dir, "bad.safetensors")
        rc = convert_to_bf16.main(["--src", self.src, "--dst", bad, "--expect-sha256", "0" * 64])
        self.assertEqual(rc, 2)
        self.assertFalse(os.path.exists(bad))
        self.assertFalse(os.path.exists(bad + ".partial"))


class TestStaticFiles(unittest.TestCase):
    def test_test_input_json_is_valid_for_both_variants(self):
        with open(os.path.join(WORKER, "test_input.json")) as fh:
            inp = json.load(fh)["input"]
        for spec in (A14B, TI2V):
            plan = handler.validate_and_build(inp, spec)
            self.assertEqual(plan["num_shots"], 2)

    def test_download_manifest_matches_handler_revisions(self):
        with open(os.path.join(WORKER, "download_models.sh")) as fh:
            script = fh.read()
        for spec in (A14B, TI2V):
            self.assertIn(spec["revision"], script)
            self.assertIn(spec["repo"], script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
