"""
Integração REAL com diffusers (CPU, modelos Wan minúsculos e aleatórios, mesmo layout
-Diffusers do Hugging Face). Prova, sem GPU e sem baixar pesos, que:

  * o _load_engine monta o pipeline como o diffusers espera (A14B com dois experts e
    boundary_ratio; 5B com expand_timesteps e sem transformer_2);
  * gerar com os embeddings pré-calculados pelo WanEngine dá o MESMO vídeo que o
    WanPipeline padrão chamado com o prompt em texto (mesmo seed, shift e guidance);
  * o mesmo seed reproduz o mesmo vídeo; o flow_shift pedido chega ao scheduler;
  * o VAE em tiles funciona nas duas variantes;
  * shards convertidos por convert_to_bf16.py (com --keep-fp32) carregam bit a bit iguais
    ao F32 original carregado com torch_dtype=bfloat16, inclusive via device_map.

Pulado automaticamente se torch/diffusers/transformers/accelerate não estiverem
instalados (os testes de mock cobrem o resto).
"""

from __future__ import annotations

import glob
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.dirname(HERE)
sys.path.insert(0, WORKER)

HAVE_STACK = all(importlib.util.find_spec(m) for m in ("torch", "diffusers", "transformers", "accelerate", "tokenizers"))

KEEP = "time_embedder,scale_shift_table,norm1,norm2,norm3"
SCHEDULER = {  # cópia dos scheduler_config.json fixados (só flow_shift muda entre as variantes)
    "_class_name": "UniPCMultistepScheduler", "beta_end": 0.02, "beta_schedule": "linear",
    "beta_start": 0.0001, "disable_corrector": [], "dynamic_thresholding_ratio": 0.995,
    "final_sigmas_type": "zero", "lower_order_final": True, "num_train_timesteps": 1000,
    "predict_x0": True, "prediction_type": "flow_prediction", "rescale_betas_zero_snr": False,
    "sample_max_value": 1.0, "solver_order": 2, "solver_p": None, "solver_type": "bh2",
    "steps_offset": 0, "thresholding": False, "time_shift_type": "exponential",
    "timestep_spacing": "linspace", "trained_betas": None, "use_beta_sigmas": False,
    "use_dynamic_shifting": False, "use_exponential_sigmas": False, "use_flow_sigmas": True,
    "use_karras_sigmas": False,
}
MODEL_INDEX = {
    "a14b": {"_class_name": "WanPipeline", "boundary_ratio": 0.875,
             "scheduler": ["diffusers", "UniPCMultistepScheduler"],
             "text_encoder": ["transformers", "UMT5EncoderModel"], "tokenizer": ["transformers", "T5TokenizerFast"],
             "transformer": ["diffusers", "WanTransformer3DModel"],
             "transformer_2": ["diffusers", "WanTransformer3DModel"], "vae": ["diffusers", "AutoencoderKLWan"]},
    "ti2v-5b": {"_class_name": "WanPipeline", "boundary_ratio": None, "expand_timesteps": True,
                "scheduler": ["diffusers", "UniPCMultistepScheduler"],
                "text_encoder": ["transformers", "UMT5EncoderModel"], "tokenizer": ["transformers", "T5TokenizerFast"],
                "transformer": ["diffusers", "WanTransformer3DModel"], "transformer_2": [None, None],
                "vae": ["diffusers", "AutoencoderKLWan"]},
}
WORDS = ("a the of and in on to with wide shot close up woman yellow raincoat street night rain neon "
         "face hood light camera walks toward calm eyes cinematic style lighthouse keeper beard cap "
         "coast dusk waves lantern glow harbor dawn road desert static")


def _build_tiny_repo(path: str, variant: str) -> str:
    """Escreve um repositório -Diffusers minúsculo; os transformers saem em F32 e são
    convertidos por convert_to_bf16.py exatamente como o download_models.sh faz."""
    import torch
    from diffusers import AutoencoderKLWan, WanTransformer3DModel
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast, UMT5Config, UMT5EncoderModel

    import convert_to_bf16

    os.makedirs(os.path.join(path, "scheduler"), exist_ok=True)
    with open(os.path.join(path, "model_index.json"), "w") as fh:
        json.dump(MODEL_INDEX[variant], fh)
    sched = dict(SCHEDULER, flow_shift=3.0 if variant == "a14b" else 5.0)
    with open(os.path.join(path, "scheduler", "scheduler_config.json"), "w") as fh:
        json.dump(sched, fh)

    vocab = {"<pad>": 0, "</s>": 1, "<unk>": 2}
    for w in WORDS.split():
        vocab.setdefault(w, len(vocab))
    tok = Tokenizer(models.WordLevel(vocab=vocab, unk_token="<unk>"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    PreTrainedTokenizerFast(tokenizer_object=tok, pad_token="<pad>", eos_token="</s>", unk_token="<unk>",
                            model_max_length=512).save_pretrained(os.path.join(path, "tokenizer"))

    torch.manual_seed(0)
    te = UMT5EncoderModel(UMT5Config(vocab_size=128, d_model=32, d_kv=8, d_ff=64, num_layers=2, num_heads=4,
                                     relative_attention_num_buckets=8, feed_forward_proj="gated-gelu"))
    te.to(torch.bfloat16).save_pretrained(os.path.join(path, "text_encoder"), max_shard_size="200KB",
                                          safe_serialization=True)

    channels = 16 if variant == "a14b" else 48
    experts = ["transformer", "transformer_2"] if variant == "a14b" else ["transformer"]
    fp32_root = path + "-fp32"
    for seed, name in enumerate(experts, start=1):
        torch.manual_seed(seed)
        t = WanTransformer3DModel(patch_size=(1, 2, 2), num_attention_heads=2, attention_head_dim=12,
                                  in_channels=channels, out_channels=channels, text_dim=32, freq_dim=256,
                                  ffn_dim=32, num_layers=2, cross_attn_norm=True,
                                  qk_norm="rms_norm_across_heads", rope_max_seq_len=32)
        src = os.path.join(fp32_root, name)
        t.save_pretrained(src, max_shard_size="40KB", safe_serialization=True)
        dst = os.path.join(path, name)
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(src):
            if f.endswith(".safetensors"):
                assert convert_to_bf16.main(["--src", os.path.join(src, f), "--dst", os.path.join(dst, f),
                                             "--keep-fp32", KEEP]) == 0
            else:
                shutil.copy(os.path.join(src, f), os.path.join(dst, f))

    torch.manual_seed(7)
    if variant == "a14b":
        vae = AutoencoderKLWan(base_dim=3, z_dim=16, dim_mult=[1, 1, 1, 1], num_res_blocks=1,
                               temperal_downsample=[False, True, True])
    else:
        vae = AutoencoderKLWan(base_dim=3, z_dim=48, in_channels=12, out_channels=12, is_residual=True,
                               patch_size=2, latents_mean=[0.0] * 48, latents_std=[1.0] * 48,
                               dim_mult=[1, 1, 1, 1], num_res_blocks=1, scale_factor_spatial=16,
                               scale_factor_temporal=4, temperal_downsample=[False, True, True])
    vae.save_pretrained(os.path.join(path, "vae"), safe_serialization=True)
    with open(os.path.join(path, ".cineforge_ready"), "w") as fh:
        import handler

        fh.write(f"revision={handler.VARIANTS[variant]['revision']}\n")
    return fp32_root


@unittest.skipUnless(HAVE_STACK, "torch/diffusers/transformers/accelerate ausentes")
class TinyWanCpuBase(unittest.TestCase):
    variant = "a14b"
    size = 32

    @classmethod
    def setUpClass(cls):
        import handler

        cls.handler = handler
        cls.root = tempfile.mkdtemp(prefix=f"tinywan-{cls.variant}-")
        cls.path = os.path.join(cls.root, "model")
        cls.fp32_root = _build_tiny_repo(cls.path, cls.variant)

    def setUp(self):
        h = self.handler
        self._saved = {k: getattr(h, k) for k in (
            "DEVICE", "MODEL_DIR_OVERRIDE", "MIN_SIDE", "VARIANT", "SPEC", "PIPELINE_FACTORY",
            "TOKENIZER_FACTORY", "ENCODER", "VAE_TILING")}
        h.DEVICE = "cpu"
        h.MODEL_DIR_OVERRIDE = self.path
        h.MIN_SIDE = 32
        h.VARIANT = self.variant
        h.SPEC = h.VARIANTS[self.variant]
        h.PIPELINE_FACTORY = h._load_engine
        h.TOKENIZER_FACTORY = h._load_tokenizer
        h._ENGINE = None
        h._TOKENIZER = None
        h._TOKENIZER_FAILED = False
        self.captured = []
        real_encoder = self._saved["ENCODER"]

        def capture(frames, fps, crf, out_path):
            self.captured.append(np.array(frames, copy=True))
            return real_encoder(frames, fps, crf, out_path)

        h.ENCODER = capture

    def tearDown(self):
        for k, v in self._saved.items():
            setattr(self.handler, k, v)
        self.handler._ENGINE = None
        self.handler._TOKENIZER = None

    def tiny_input(self, **over):
        inp = {"global_caption": "a woman in a yellow raincoat on a neon street at night. This scene contains 2 shots.",
               "shot_captions": ["wide shot of the woman walks toward the camera", "close up of the face"],
               "num_frames": 17, "seed": 42, "height": self.size, "width": self.size,
               "num_inference_steps": 4, "output_path": "teste/tiny.mp4"}
        inp.update(over)
        return inp


class TestTinyA14B(TinyWanCpuBase):
    variant = "a14b"
    size = 32

    def test_end_to_end_two_shots(self):
        out = self.handler.handler({"id": "tiny", "input": self.tiny_input()})
        self.assertNotIn("error", out, out.get("error"))
        self.assertEqual(out["frames"], 17)
        self.assertEqual([s["frames_used"] for s in out["shots"]], [9, 8])
        self.assertEqual([s["frames_generated"] for s in out["shots"]], [9, 9])
        self.assertEqual(out["worker"]["offload"], "none")
        self.assertEqual(out["worker"]["boundary_ratio"], 0.875)
        self.assertEqual(out["flow_shift"], 12.0)
        self.assertTrue(out["prompt_tokens_exact"])
        self.assertEqual(self.captured[0].shape, (17, 32, 32, 3))
        self.assertEqual(self.captured[0].dtype, np.uint8)
        engine = self.handler._ENGINE
        self.assertEqual(engine.pipe.scheduler.config.flow_shift, 12.0)
        self.assertIsNotNone(engine.pipe.transformer_2)

    def test_same_seed_same_video(self):
        a = self.handler.handler({"id": "a", "input": self.tiny_input()})
        b = self.handler.handler({"id": "b", "input": self.tiny_input()})
        self.assertNotIn("error", a)
        self.assertTrue(np.array_equal(self.captured[0], self.captured[1]))
        c = self.handler.handler({"id": "c", "input": self.tiny_input(seed=43)})
        self.assertNotIn("error", c)
        self.assertFalse(np.array_equal(self.captured[0], self.captured[2]))
        self.assertEqual(a["sha256"], b["sha256"])

    def test_precomputed_embeddings_match_standard_pipeline(self):
        import torch
        from diffusers import UniPCMultistepScheduler, WanPipeline

        h = self.handler
        out = h.handler({"id": "eq", "input": self.tiny_input()})
        self.assertNotIn("error", out, out.get("error"))
        engine = h._ENGINE
        plan = h.validate_and_build(self.tiny_input(), h.SPEC)
        shot0 = plan["shots"][0]
        ref_pipe = WanPipeline(
            tokenizer=engine.text_pipe.tokenizer, text_encoder=engine.text_pipe.text_encoder,
            vae=engine.pipe.vae,
            scheduler=UniPCMultistepScheduler.from_config(engine.base_scheduler_config, flow_shift=12.0),
            transformer=engine.pipe.transformer, transformer_2=engine.pipe.transformer_2, boundary_ratio=0.875)
        ref_pipe.set_progress_bar_config(disable=True)
        video = ref_pipe(prompt=shot0["prompt"], negative_prompt=h.DEFAULT_NEGATIVE_PROMPT,
                         height=32, width=32, num_frames=9, num_inference_steps=4,
                         guidance_scale=4.0, guidance_scale_2=3.0,
                         generator=torch.Generator(device="cpu").manual_seed(shot0["seed"]),
                         output_type="np").frames[0]
        ref = (np.clip(video, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
        got = self.captured[0][:9]
        self.assertEqual(ref.shape, got.shape)
        diff = int(np.abs(ref.astype(int) - got.astype(int)).max())
        # Embeddings em lote (2 prompts) vs 1 prompt podem diferir no último bit do bf16;
        # o vídeo tem que ser o mesmo a menos de arredondamento.
        self.assertLessEqual(diff, 2, f"diferença máxima {diff}")

    def test_flow_shift_and_vae_tiling(self):
        out = self.handler.handler({"id": "fs", "input": self.tiny_input(flow_shift=5.0)})
        self.assertNotIn("error", out, out.get("error"))
        engine = self.handler._ENGINE
        self.assertEqual(engine.pipe.scheduler.config.flow_shift, 5.0)
        engine.pipe.vae.enable_tiling(tile_sample_min_height=16, tile_sample_min_width=16,
                                      tile_sample_stride_height=8, tile_sample_stride_width=8)
        engine.vae_tiling = True
        tiled = self.handler.handler({"id": "tile", "input": self.tiny_input()})
        self.assertNotIn("error", tiled, tiled.get("error"))
        self.assertEqual(self.captured[-1].shape, (17, 32, 32, 3))

    def test_converted_weights_equal_fp32_loaded_as_bf16(self):
        import torch
        from diffusers import WanTransformer3DModel

        for name in ("transformer", "transformer_2"):
            ref = WanTransformer3DModel.from_pretrained(os.path.join(self.fp32_root, name), torch_dtype=torch.bfloat16)
            got = WanTransformer3DModel.from_pretrained(self.path, subfolder=name, torch_dtype=torch.bfloat16,
                                                        device_map="cpu", local_files_only=True)
            sd_ref, sd_got = ref.state_dict(), got.state_dict()
            self.assertEqual(set(sd_ref), set(sd_got))
            kept = 0
            for key, tensor in sd_ref.items():
                self.assertEqual(sd_got[key].dtype, tensor.dtype, key)
                self.assertTrue(torch.equal(sd_got[key], tensor), key)
                kept += tensor.dtype == torch.float32
            self.assertGreater(kept, 0)  # time_embedder/scale_shift_table/norm2 continuam FP32
            shards = glob.glob(os.path.join(self.path, name, "*.safetensors"))
            self.assertGreater(len(shards), 1)  # o caminho com index.json foi exercitado


class TestTinyTi2v5B(TinyWanCpuBase):
    variant = "ti2v-5b"
    size = 64

    def test_end_to_end_two_shots_expand_timesteps(self):
        out = self.handler.handler({"id": "tiny5b", "input": self.tiny_input()})
        self.assertNotIn("error", out, out.get("error"))
        self.assertEqual(out["frames"], 17)
        self.assertEqual(out["fps"], 24)
        self.assertIsNone(out["cfg_scale_2"])
        self.assertEqual(out["flow_shift"], 5.0)
        engine = self.handler._ENGINE
        self.assertIsNone(engine.pipe.transformer_2)
        self.assertTrue(engine.pipe.config.expand_timesteps)
        self.assertEqual(self.captured[0].shape, (17, 64, 64, 3))

    def test_vae_tiling_with_patch_size_2(self):
        out = self.handler.handler({"id": "a", "input": self.tiny_input()})
        self.assertNotIn("error", out, out.get("error"))
        engine = self.handler._ENGINE
        engine.pipe.vae.enable_tiling(tile_sample_min_height=32, tile_sample_min_width=32,
                                      tile_sample_stride_height=16, tile_sample_stride_width=16)
        engine.vae_tiling = True
        tiled = self.handler.handler({"id": "b", "input": self.tiny_input()})
        self.assertNotIn("error", tiled, tiled.get("error"))
        self.assertEqual(self.captured[-1].shape, (17, 64, 64, 3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
