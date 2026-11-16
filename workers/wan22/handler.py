"""
CineForge AI — worker RunPod Serverless para Wan 2.2 (diffusers), multi-shot.

Contrato de entrada (job["input"]) — o MESMO do worker HoloCine, para o hermes_api.py
/gerar-cena e o cliente da VPS não mudarem:

  global_caption   str        obrigatório (modo estruturado)
  shot_captions    list[str]  obrigatório, 1..13 planos
  num_frames       int        total do vídeo; padrão 81 (a14b) / 121 (ti2v-5b);
                              corrigido para 4t+1 (enforce_4t_plus_1, como no HoloCine)
  shot_cut_frames  list[int]  opcional; [] ou ausente = cortes automáticos
  negative_prompt  str        opcional; padrão = negativo oficial do Wan 2.2 (chinês)
  seed             int        opcional; 0 ou ausente = aleatório (o seed real volta na saída)
  output_path      str        opcional; vira o nome do arquivo (cópia no volume só se
                              WAN_SAVE_OUTPUTS=1)

Opcionais extras (todos com limites): prompt (modo bruto do HoloCine
"[global caption] ... [per shot caption] ... [shot cut] ..."), num_inference_steps,
cfg_scale (expert de ruído alto no A14B), cfg_scale_2 (expert de ruído baixo, só A14B),
flow_shift, fps, height, width, crf, return_base64, allow_prompt_truncation,
output_upload_url (URL presigned PUT https), output_upload_content_type.

Saída de sucesso (o pipeline da VPS lê output["video_b64"]):
  {"video_b64": "<mp4 base64>", "mime_type": "video/mp4", "file_name": ..., "frames": ...,
   "fps": ..., "seconds": ..., "seed": ..., "shots": [...], "elapsed_s": ..., ...}
Saída de erro: {"error": "..."} -> o RunPod marca o job como FAILED.

Motor (variável MODEL_VARIANT):
  a14b     -> Wan-AI/Wan2.2-T2V-A14B-Diffusers (MoE: 2 experts de 14B; GPU de 80 GB)
  ti2v-5b  -> Wan-AI/Wan2.2-TI2V-5B-Diffusers  (5B; testes baratos em GPU de 24-48 GB)
Ambos Apache-2.0. Pesos lidos só do Network Volume (/runpod-volume).

Multi-shot: cada plano é gerado separadamente com prompt = global caption + caption do
plano. O trecho de cada plano (definido por shot_cut_frames) é arredondado PARA CIMA até
4k+1 (exigência do VAE do Wan), gerado com seed próprio derivado do seed do job, e
aparado de volta ao tamanho do trecho; os planos são concatenados como cortes secos e
codificados num único H.264 (ffmpeg/libx264, yuv420p, +faststart).

Regras: nenhum segredo neste worker; nenhum download, git clone ou pip install em
runtime (HF_HUB_OFFLINE=1); nada de trust_remote_code.
"""

from __future__ import annotations

import base64
import gc
import hashlib
import html
import ipaddress
import json
import logging
import os
import random
import re
import shutil
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

try:  # o SDK existe na imagem; os testes locais rodam sem ele
    import runpod  # type: ignore
except ImportError:  # pragma: no cover - depende do ambiente
    runpod = None  # type: ignore

logging.basicConfig(
    level=os.environ.get("WAN_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("wan22-worker")

# ---------------------------------------------------------------------------
# Variantes do modelo (fatos verificados no Hugging Face e no repositório oficial)
# ---------------------------------------------------------------------------

# Negativo oficial do Wan 2.2 (wan/configs/shared_config.py, sample_neg_prompt).
DEFAULT_NEGATIVE_PROMPT = (
    "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，"
    "最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，"
    "画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，"
    "杂乱的背景，三条腿，背景人很多，倒着走"
)

VARIANTS: Dict[str, Dict[str, Any]] = {
    "a14b": {
        "repo": "Wan-AI/Wan2.2-T2V-A14B-Diffusers",
        "revision": "5be7df9619b54f4e2667b2755bc6a756675b5cd7",
        "dir": "Wan2.2-T2V-A14B-Diffusers",
        "two_experts": True,
        # wan/configs/wan_t2v_A14B.py: 40 passos, guide (baixo 3.0, alto 4.0), shift 12.0, 16 fps
        "defaults": {"num_inference_steps": 40, "cfg_scale": 4.0, "cfg_scale_2": 3.0,
                     "flow_shift": 12.0, "fps": 16, "height": 480, "width": 832, "crf": 23},
        "default_frames": 81,      # frame_num oficial (5 s a 16 fps)
        "max_shot_frames": 81,     # duração de treino; planos maiores degradam
        "size_multiple": 16,       # VAE 8x + patch 2
        "max_pixels": 720 * 1280,
        "official_sizes": {(480, 832), (832, 480), (720, 1280), (1280, 720)},
        # Tabela oficial Wan 2.2: 81 frames 480P, 40 passos = 785,7 s em A100 (pior GPU de 80 GB)
        "ref_seconds": 786.0, "ref_frames": 81, "ref_pixels": 480 * 832, "ref_steps": 40,
        "max_gen_seconds": 3000.0,   # endpoint com Execution timeout 3600 s (RUNBOOK §9)
    },
    "ti2v-5b": {
        "repo": "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
        "revision": "b8fff7315c768468a5333511427288870b2e9635",
        "dir": "Wan2.2-TI2V-5B-Diffusers",
        "two_experts": False,
        # wan/configs/wan_ti2v_5B.py: 50 passos, guide 5.0, shift 5.0, 24 fps, 121 frames
        "defaults": {"num_inference_steps": 50, "cfg_scale": 5.0, "cfg_scale_2": None,
                     "flow_shift": 5.0, "fps": 24, "height": 704, "width": 1280, "crf": 23},
        "default_frames": 121,
        "max_shot_frames": 121,
        "size_multiple": 32,       # VAE 16x + patch 2
        "max_pixels": 704 * 1280,
        "official_sizes": {(704, 1280), (1280, 704)},
        # Tabela oficial: 121 frames 720P, 50 passos = 534,7 s em RTX 4090; folga para A40
        "ref_seconds": 600.0, "ref_frames": 121, "ref_pixels": 704 * 1280, "ref_steps": 50,
        "max_gen_seconds": 1500.0,   # endpoint com Execution timeout 1800 s (RUNBOOK §6)
    },
}

# VRAM mínima (GB decimais, como torch reporta) e RAM de host por (variante, modo).
#  none  = tudo residente na GPU
#  t5    = transformers + VAE residentes; o T5 (11,4 GB) fica na RAM e sobe à GPU só
#          para codificar os prompts do job
#  model = diffusers enable_model_cpu_offload (um componente por vez na GPU)
RESOURCES: Dict[Tuple[str, str], Dict[str, float]] = {
    ("a14b", "none"): {"vram": 78.0, "ram": 16.0},
    ("a14b", "t5"): {"vram": 75.0, "ram": 24.0},
    ("a14b", "model"): {"vram": 44.0, "ram": 80.0},
    ("ti2v-5b", "none"): {"vram": 40.0, "ram": 16.0},
    ("ti2v-5b", "t5"): {"vram": 30.0, "ram": 24.0},
    ("ti2v-5b", "model"): {"vram": 22.0, "ram": 34.0},
}
OFFLOAD_MODES = ("auto", "none", "t5", "model")
TEXT_LEN = 512  # wan_shared_cfg.text_len; max_sequence_length do diffusers

# ---------------------------------------------------------------------------
# Configuração (somente variáveis de ambiente não secretas)
# ---------------------------------------------------------------------------


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw not in (None, "") else default


def _env_float(name: str, default: Optional[float]) -> Optional[float]:
    raw = os.environ.get(name)
    return float(raw) if raw not in (None, "") else default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "sim", "on")


VARIANT = os.environ.get("MODEL_VARIANT", "a14b").strip().lower()
SPEC: Dict[str, Any] = VARIANTS.get(VARIANT, VARIANTS["a14b"])
MODEL_ROOT = os.environ.get("WAN_MODEL_ROOT", "/runpod-volume/wan22")
MODEL_DIR_OVERRIDE = os.environ.get("WAN_MODEL_DIR", "")
OUTPUT_DIR = os.environ.get("WAN_OUTPUT_DIR", "/runpod-volume/wan22/outputs")
DEVICE = os.environ.get("WAN_DEVICE", "cuda").strip().lower()
OFFLOAD = os.environ.get("WAN_OFFLOAD", "auto").strip().lower()
VAE_TILING = os.environ.get("WAN_VAE_TILING", "auto").strip().lower()

MAX_SHOTS = _env_int("WAN_MAX_SHOTS", 13)
MIN_FRAMES = _env_int("WAN_MIN_FRAMES", 17)
MAX_FRAMES = _env_int("WAN_MAX_FRAMES", 481)
MIN_SHOT_FRAMES = _env_int("WAN_MIN_SHOT_FRAMES", 8)
MAX_STEPS = _env_int("WAN_MAX_STEPS", 60)
MIN_SIDE = _env_int("WAN_MIN_SIDE", 256)
MAX_SIDE = _env_int("WAN_MAX_SIDE", 1280)
MAX_PROMPT_TOKENS = _env_int("WAN_MAX_PROMPT_TOKENS", TEXT_LEN)
# /run aceita no máximo 10 MB de resultado; deixamos folga para o JSON de metadados.
MAX_INLINE_B64 = _env_int("WAN_MAX_INLINE_B64_BYTES", 9_000_000)
MIN_RAM_OVERRIDE = _env_float("WAN_MIN_RAM_GB", None)
SAVE_OUTPUTS = _env_bool("WAN_SAVE_OUTPUTS", False)
EAGER_LOAD = _env_bool("WAN_EAGER_LOAD", False)

RESERVED_TAGS = ("[global caption]", "[per shot caption]", "[shot cut]")
SCENE_PHRASE_RE = re.compile(r"This scene contains\s+(\d+)\s+shots?\.?", re.IGNORECASE)
KEEP_FP32_PATTERNS = ("time_embedder", "scale_shift_table", "norm1", "norm2", "norm3")
ALLOWED_INPUT_KEYS = {
    "global_caption", "shot_captions", "num_frames", "shot_cut_frames", "negative_prompt",
    "seed", "output_path", "prompt", "num_inference_steps", "cfg_scale", "cfg_scale_2",
    "flow_shift", "fps", "height", "width", "crf", "return_base64",
    "allow_prompt_truncation", "output_upload_url", "output_upload_content_type",
}


class InputError(ValueError):
    """Erro de validação de entrada: devolvido ao cliente sem gastar GPU."""


# Limites que dependem da variante (lidos na hora; WAN_* no ambiente sobrepõe).
def default_frames(spec: Dict[str, Any]) -> int:
    return _env_int("WAN_DEFAULT_FRAMES", spec["default_frames"])


def max_shot_frames(spec: Dict[str, Any]) -> int:
    return _env_int("WAN_MAX_SHOT_FRAMES", spec["max_shot_frames"])


def max_pixels(spec: Dict[str, Any]) -> int:
    return _env_int("WAN_MAX_PIXELS", spec["max_pixels"])


def max_gen_seconds(spec: Dict[str, Any]) -> float:
    return float(_env_float("WAN_MAX_GEN_SECONDS", spec["max_gen_seconds"]))


def estimate_gen_seconds(spec: Dict[str, Any], shot_frames: Sequence[int], pixels: int, steps: int) -> float:
    """Estimativa conservadora do tempo de GPU: linear em frames e passos, pixels^1,4
    (a atenção cresce mais que linear: 720P/480P = 2,3x pixels e ~3,2–3,5x tempo na tabela
    oficial). WAN_REF_SECONDS ajusta a referência à GPU real depois do primeiro teste."""
    ref = float(_env_float("WAN_REF_SECONDS", spec["ref_seconds"]))
    scale = (pixels / spec["ref_pixels"]) ** 1.4 * (steps / spec["ref_steps"])
    return sum(ref * scale * f / spec["ref_frames"] for f in shot_frames)


def flow_shift_default(spec: Dict[str, Any]) -> float:
    return float(_env_float("WAN_FLOW_SHIFT", spec["defaults"]["flow_shift"]))


# ---------------------------------------------------------------------------
# Matemática de frames e planos
# ---------------------------------------------------------------------------

def enforce_4t_plus_1(n: int) -> int:
    """Força n para a forma 4t+1 mais próxima (mesma regra do worker HoloCine)."""
    t = round((n - 1) / 4)
    return 4 * t + 1


def snap_up_4k1(n: int) -> int:
    """Menor 4k+1 >= n (o VAE do Wan comprime 4 frames por latente + 1 inicial)."""
    n = max(int(n), 1)
    return 4 * ((n - 1 + 3) // 4) + 1


def auto_shot_cuts(total_frames: int, num_shots: int) -> List[int]:
    """Cortes uniformes em posições 4t+1 (igual ao worker HoloCine)."""
    cuts: List[int] = []
    if num_shots > 1:
        ideal_step = total_frames / num_shots
        for i in range(1, num_shots):
            cuts.append(enforce_4t_plus_1(round(i * ideal_step)))
    return cuts


def shot_segments(total_frames: int, cuts: Sequence[int]) -> List[Tuple[int, int]]:
    """[(início, comprimento)] de cada plano a partir dos cortes."""
    bounds = [0] + list(cuts) + [total_frames]
    return [(a, b - a) for a, b in zip(bounds, bounds[1:])]


def derive_shot_seed(seed: int, index: int) -> int:
    """Seed determinístico por plano: plano 0 usa o próprio seed; os demais variam."""
    modulus = 2**31 - 1
    return ((seed - 1 + 1_000_003 * index) % modulus) + 1


def _normalize_cuts(raw_cuts: List[int], total_frames: int, num_shots: int) -> List[int]:
    processed = [enforce_4t_plus_1(int(f)) for f in raw_cuts]
    if len(set(processed)) != len(processed) or processed != sorted(processed):
        raise InputError(
            f"shot_cut_frames precisa ser crescente e sem repetição após 4t+1: {processed}"
        )
    for f in processed:
        if not 0 < f < total_frames:
            raise InputError(f"corte {f} fora do intervalo (0, {total_frames})")
    if len(processed) != num_shots - 1:
        raise InputError(
            f"shot_cut_frames tem {len(processed)} cortes, mas {num_shots} planos exigem "
            f"{num_shots - 1}. Envie [] para cortes automáticos."
        )
    return processed


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def _check_int(value: Any, name: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise InputError(f"{name} precisa ser inteiro")
    value = int(value)
    if not lo <= value <= hi:
        raise InputError(f"{name}={value} fora do intervalo [{lo}, {hi}]")
    return value


def _check_float(value: Any, name: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{name} precisa ser número")
    value = float(value)
    if not lo <= value <= hi:
        raise InputError(f"{name}={value} fora do intervalo [{lo}, {hi}]")
    return value


def _check_text(value: Any, name: str, max_len: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{name} precisa ser texto não vazio")
    if len(value) > max_len:
        raise InputError(f"{name} excede {max_len} caracteres")
    return value.strip()


def safe_relative_mp4(path: Any) -> str:
    """Sanitiza output_path (relativo, sem '..', só [A-Za-z0-9._/-], termina em .mp4)."""
    if not isinstance(path, str) or not path.strip():
        raise InputError("output_path precisa ser texto")
    p = path.strip().replace("\\", "/")
    if p.startswith("/") or re.match(r"^[A-Za-z]:", p):
        raise InputError("output_path precisa ser relativo")
    parts = [seg for seg in p.split("/") if seg not in ("", ".")]
    if not parts or any(seg == ".." for seg in parts):
        raise InputError("output_path inválido")
    if any(not re.fullmatch(r"[A-Za-z0-9._-]+", seg) for seg in parts):
        raise InputError("output_path só aceita letras, números, '.', '_', '-' e '/'")
    rel = "/".join(parts)
    if not rel.lower().endswith(".mp4"):
        rel += ".mp4"
    return rel


def _validate_upload_url(url: Any) -> str:
    if not isinstance(url, str) or not url:
        raise InputError("output_upload_url precisa ser texto")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise InputError("output_upload_url precisa ser uma URL presigned https")
    host = parsed.hostname
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:  # é um hostname, não um IP literal
        ip = None
    internal = (
        (ip is not None and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved))
        or (ip is None and (host == "localhost" or host.endswith((".local", ".internal", ".localhost"))))
    )
    if internal:
        raise InputError("output_upload_url não pode apontar para rede interna")
    return url


def _latin_non_ascii_ratio(texts: List[str]) -> float:
    """Fração de letras não-ASCII fora do bloco CJK (chinês é um idioma nativo do Wan)."""
    letters = [c for t in texts for c in t if c.isalpha() and not ("一" <= c <= "鿿")]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) > 127) / len(letters)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def compose_shot_prompt(global_text: str, shot_caption: str) -> str:
    """Prompt de cada plano: global caption (contexto) + caption do plano."""
    return _collapse(f"{global_text} {shot_caption}")


def parse_raw_prompt(prompt: str) -> Tuple[str, List[str]]:
    """Converte o modo bruto do HoloCine em (global_caption, shot_captions)."""
    if not prompt.startswith("[global caption]") or "[per shot caption]" not in prompt:
        raise InputError("prompt bruto precisa seguir '[global caption] ... [per shot caption] ...'")
    head, _, tail = prompt.partition("[per shot caption]")
    global_caption = head[len("[global caption]"):].strip()
    shots = [s.strip() for s in tail.split("[shot cut]")]
    if not global_caption or any(not s for s in shots):
        raise InputError("prompt bruto com global caption ou plano vazio")
    return global_caption, shots


def validate_and_build(inp: Any, spec: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Valida o input e devolve o plano de geração (sem tocar na GPU)."""
    spec = spec or SPEC
    defaults = spec["defaults"]
    if not isinstance(inp, dict):
        raise InputError("input precisa ser um objeto JSON")
    warnings: List[str] = []
    unknown = sorted(set(inp) - ALLOWED_INPUT_KEYS)
    if unknown:
        warnings.append(f"campos ignorados: {', '.join(unknown)}")

    shot_cap = max_shot_frames(spec)
    pixel_cap = max_pixels(spec)
    num_frames_in = inp.get("num_frames", default_frames(spec))
    num_frames_in = _check_int(num_frames_in, "num_frames", MIN_FRAMES, MAX_FRAMES)
    num_frames = enforce_4t_plus_1(num_frames_in)
    if num_frames > MAX_FRAMES:
        num_frames -= 4
    if num_frames != num_frames_in:
        warnings.append(f"num_frames corrigido {num_frames_in} -> {num_frames} (4t+1)")

    raw_cuts = inp.get("shot_cut_frames")
    if raw_cuts is not None and not isinstance(raw_cuts, list):
        raise InputError("shot_cut_frames precisa ser lista de inteiros")
    if raw_cuts:
        raw_cuts = [_check_int(f, "shot_cut_frames[i]", 1, MAX_FRAMES) for f in raw_cuts]

    global_caption = inp.get("global_caption")
    shot_captions = inp.get("shot_captions")
    raw_prompt = inp.get("prompt")

    if global_caption is not None or shot_captions is not None:
        mode = "structured"
        gc_text = _check_text(global_caption, "global_caption")
        if not isinstance(shot_captions, list) or not shot_captions:
            raise InputError("shot_captions precisa ser lista com pelo menos 1 plano")
        if len(shot_captions) > MAX_SHOTS:
            raise InputError(f"máximo de {MAX_SHOTS} planos (recebido {len(shot_captions)})")
        shots = [_check_text(s, f"shot_captions[{i}]", 1200) for i, s in enumerate(shot_captions)]
    elif raw_prompt is not None:
        mode = "raw"
        gc_text, shots = parse_raw_prompt(_check_text(raw_prompt, "prompt", 8000))
        if len(shots) > MAX_SHOTS:
            raise InputError(f"máximo de {MAX_SHOTS} planos (recebido {len(shots)})")
    else:
        raise InputError("envie global_caption + shot_captions (ou prompt no formato bruto)")

    for text in [gc_text] + shots:
        for tag in RESERVED_TAGS:
            if tag in text.lower():
                raise InputError(f"o texto não pode conter a tag reservada {tag}")
    num_shots = len(shots)
    found = SCENE_PHRASE_RE.search(gc_text)
    if found and int(found.group(1)) != num_shots:
        raise InputError(f"global_caption diz {found.group(1)} planos, mas shot_captions tem {num_shots}")
    if not found and "this scene contains" in gc_text.lower():
        raise InputError("frase 'This scene contains N shots.' malformada na global_caption")
    # A frase é do HoloCine; para o Wan ela some (cada chamada gera UM plano).
    global_text = _collapse(SCENE_PHRASE_RE.sub(" ", gc_text))
    if not global_text:
        raise InputError("global_caption ficou vazia após remover 'This scene contains N shots.'")
    if _latin_non_ascii_ratio([gc_text] + shots) > 0.05:
        warnings.append("captions parecem não estar em inglês; o Wan 2.2 responde melhor em inglês ou chinês")

    if raw_cuts:
        shot_cut_frames = _normalize_cuts(raw_cuts, num_frames, num_shots)
    else:
        shot_cut_frames = auto_shot_cuts(num_frames, num_shots)
        if (len(set(shot_cut_frames)) != num_shots - 1
                or any(not 0 < f < num_frames for f in shot_cut_frames)):
            raise InputError(
                f"num_frames={num_frames} é pouco para {num_shots} planos; aumente num_frames "
                "ou reduza o número de planos"
            )

    segments = shot_segments(num_frames, shot_cut_frames)
    shot_plans: List[Dict[str, Any]] = []
    for i, (start, length) in enumerate(segments):
        if length < MIN_SHOT_FRAMES:
            raise InputError(
                f"o plano {i + 1} ficou com {length} frames (< {MIN_SHOT_FRAMES}); "
                "aumente num_frames ou ajuste shot_cut_frames"
            )
        gen_frames = snap_up_4k1(length)
        if gen_frames > shot_cap:
            raise InputError(
                f"o plano {i + 1} ficou com {length} frames; o Wan 2.2 gera no máximo "
                f"{shot_cap} por plano. Use mais planos, cortes mais próximos ou "
                f"reduza num_frames"
            )
        shot_plans.append({"index": i, "start_frame": start, "frames_used": length,
                           "frames_generated": gen_frames,
                           "prompt": compose_shot_prompt(global_text, shots[i])})

    negative = inp.get("negative_prompt")
    negative = DEFAULT_NEGATIVE_PROMPT if negative in (None, "") else _check_text(negative, "negative_prompt")

    seed_in = inp.get("seed", 0)
    seed_in = 0 if seed_in is None else _check_int(seed_in, "seed", 0, 2**31 - 1)
    seed = seed_in if seed_in > 0 else random.SystemRandom().randint(1, 2**31 - 1)
    for sp in shot_plans:
        sp["seed"] = derive_shot_seed(seed, sp["index"])

    steps = _check_int(inp.get("num_inference_steps", defaults["num_inference_steps"]),
                       "num_inference_steps", 4, MAX_STEPS)
    cfg_scale = _check_float(inp.get("cfg_scale", defaults["cfg_scale"]), "cfg_scale", 1.0, 10.0)
    if spec["two_experts"]:
        cfg_scale_2 = _check_float(inp.get("cfg_scale_2", defaults["cfg_scale_2"]), "cfg_scale_2", 1.0, 10.0)
    else:
        cfg_scale_2 = None
        if inp.get("cfg_scale_2") is not None:
            warnings.append("cfg_scale_2 ignorado: só existe no A14B (dois experts)")
    flow_shift = _check_float(inp.get("flow_shift", flow_shift_default(spec)), "flow_shift", 1.0, 20.0)
    fps = _check_int(inp.get("fps", defaults["fps"]), "fps", 1, 30)
    height = _check_int(inp.get("height", defaults["height"]), "height", MIN_SIDE, MAX_SIDE)
    width = _check_int(inp.get("width", defaults["width"]), "width", MIN_SIDE, MAX_SIDE)
    multiple = spec["size_multiple"]
    if height % multiple or width % multiple:
        raise InputError(f"height e width precisam ser múltiplos de {multiple} neste modelo")
    if height * width > pixel_cap:
        raise InputError(f"resolução {width}x{height} excede o limite de {pixel_cap} pixels")
    if (height, width) not in spec["official_sizes"]:
        sizes = ", ".join(f"{w}x{h}" for h, w in sorted(spec["official_sizes"]))
        warnings.append(f"resolução {width}x{height} fora das oficiais ({sizes}); a qualidade pode cair")
    crf = _check_int(inp.get("crf", defaults["crf"]), "crf", 15, 40)
    if cfg_scale_2 is not None and cfg_scale <= 1.0 < cfg_scale_2:
        # o diffusers liga o CFG só por guidance_scale; com cfg_scale=1 o cfg_scale_2 seria ignorado
        raise InputError("cfg_scale=1 desliga o CFG nos dois experts; use cfg_scale > 1 ou cfg_scale_2 = 1")
    est_s = estimate_gen_seconds(spec, [sp["frames_generated"] for sp in shot_plans], height * width, steps)
    budget = max_gen_seconds(spec)
    if est_s > budget:
        raise InputError(
            f"job estimado em ~{est_s / 60:.0f} min de GPU (> {budget / 60:.0f} min, limite para caber no "
            "Execution timeout do endpoint); reduza num_frames, planos, passos ou resolução, ou divida em jobs"
        )

    return_b64 = inp.get("return_base64", True)
    if not isinstance(return_b64, bool):
        raise InputError("return_base64 precisa ser true/false")
    allow_trunc = inp.get("allow_prompt_truncation", False)
    if not isinstance(allow_trunc, bool):
        raise InputError("allow_prompt_truncation precisa ser true/false")

    upload_url = inp.get("output_upload_url")
    if upload_url is not None:
        upload_url = _validate_upload_url(upload_url)
    if not return_b64 and not upload_url:
        raise InputError("return_base64=false exige output_upload_url")
    content_type = inp.get("output_upload_content_type", "video/mp4")
    if not isinstance(content_type, str) or not re.fullmatch(r"[\w.+-]+/[\w.+-]+", content_type):
        raise InputError("output_upload_content_type inválido")

    output_rel = inp.get("output_path")
    output_rel = safe_relative_mp4(output_rel) if output_rel not in (None, "") else None
    file_name = os.path.basename(output_rel) if output_rel else "wan22.mp4"

    return {
        "mode": mode,
        "global_text": global_text,
        "shots": shot_plans,
        "negative_prompt": negative,
        "num_shots": num_shots,
        "num_frames": num_frames,
        "estimated_gen_s": round(est_s, 1),
        "shot_cut_frames": shot_cut_frames,
        "seed": seed,
        "seed_requested": seed_in,
        "num_inference_steps": steps,
        "cfg_scale": cfg_scale,
        "cfg_scale_2": cfg_scale_2,
        "flow_shift": flow_shift,
        "fps": fps,
        "height": height,
        "width": width,
        "crf": crf,
        "return_base64": return_b64,
        "allow_prompt_truncation": allow_trunc,
        "upload_url": upload_url,
        "upload_content_type": content_type,
        "output_rel": output_rel,
        "file_name": file_name,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Arquivos de modelo, RAM e VRAM
# ---------------------------------------------------------------------------

def model_dir(root: Optional[str] = None, variant: Optional[str] = None) -> str:
    if MODEL_DIR_OVERRIDE:
        return MODEL_DIR_OVERRIDE
    return os.path.join(root or MODEL_ROOT, VARIANTS[variant or VARIANT]["dir"])


def resolve_model_dir(root: Optional[str] = None, variant: Optional[str] = None) -> str:
    """Confere o layout -Diffusers no volume e lista tudo o que faltar (shards inclusive)."""
    root = root or MODEL_ROOT
    variant = variant or VARIANT
    if variant not in VARIANTS:
        raise RuntimeError(f"MODEL_VARIANT inválido: {variant!r} (use a14b ou ti2v-5b)")
    path = model_dir(root, variant)
    comps = ["text_encoder", "transformer", "vae"]
    if VARIANTS[variant]["two_experts"]:
        comps.append("transformer_2")
    required = ["model_index.json", "scheduler/scheduler_config.json", "tokenizer/tokenizer.json",
                "tokenizer/tokenizer_config.json"]
    missing: List[str] = []
    for rel in required:
        if not os.path.isfile(os.path.join(path, rel)):
            missing.append(rel)
    for comp in comps:
        cdir = os.path.join(path, comp)
        if not os.path.isfile(os.path.join(cdir, "config.json")):
            missing.append(f"{comp}/config.json")
        index = [f for f in (os.listdir(cdir) if os.path.isdir(cdir) else [])
                 if f.endswith(".safetensors.index.json")]
        if index:
            try:
                with open(os.path.join(cdir, index[0])) as fh:
                    shards = sorted(set(json.load(fh)["weight_map"].values()))
            except (OSError, ValueError, KeyError) as exc:
                missing.append(f"{comp}/{index[0]} ilegível ({exc})")
                continue
            missing += [f"{comp}/{s}" for s in shards if not os.path.isfile(os.path.join(cdir, s))]
        elif not any(f.endswith(".safetensors") for f in (os.listdir(cdir) if os.path.isdir(cdir) else [])):
            missing.append(f"{comp}/*.safetensors")
    if missing:
        raise RuntimeError(
            f"arquivos do modelo {variant} ausentes em {path} (rode download_models.sh com "
            f"VARIANT={variant} no Pod; para o outro modelo mude MODEL_VARIANT): "
            + ", ".join(missing[:12]) + (" ..." if len(missing) > 12 else "")
        )
    return path


def ready_marker_ok(path: str, variant: Optional[str] = None) -> bool:
    variant = variant or VARIANT
    try:
        with open(os.path.join(path, ".cineforge_ready")) as fh:
            return VARIANTS[variant]["revision"] in fh.read()
    except OSError:
        return False


def available_ram_gb() -> float:
    """Menor valor entre MemTotal e o limite do cgroup do container."""
    total = None
    try:
        with open("/proc/meminfo") as fh:
            for line in fh:
                if line.startswith("MemTotal:"):
                    total = int(line.split()[1]) * 1024
                    break
    except OSError:
        pass
    for cg in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            with open(cg) as fh:
                raw = fh.read().strip()
            if raw.isdigit():
                limit = int(raw)
                if limit < (1 << 60):
                    total = min(total, limit) if total else limit
        except OSError:
            continue
    return (total or 0) / 1e9


def choose_offload(variant: str, vram_gb: float, requested: Optional[str] = None,
                   device: Optional[str] = None) -> str:
    """Escolhe o modo de memória; erro claro se a GPU não comporta o modelo."""
    requested = requested or OFFLOAD
    device = device or DEVICE
    if requested not in OFFLOAD_MODES:
        raise RuntimeError(f"WAN_OFFLOAD inválido: {requested!r} (use {', '.join(OFFLOAD_MODES)})")
    if not device.startswith("cuda"):
        return "none"
    if requested != "auto":
        need = RESOURCES[(variant, requested)]["vram"]
        if vram_gb < need:
            raise RuntimeError(f"GPU com {vram_gb:.0f} GB; WAN_OFFLOAD={requested} precisa de >= {need:.0f} GB")
        return requested
    order = ("t5", "model") if variant == "a14b" else ("none", "t5", "model")
    for mode in order:
        if vram_gb >= RESOURCES[(variant, mode)]["vram"]:
            return mode
    smallest = RESOURCES[(variant, order[-1])]["vram"]
    raise RuntimeError(f"GPU com {vram_gb:.0f} GB; o modelo {variant} precisa de >= {smallest:.0f} GB")


# ---------------------------------------------------------------------------
# Motor (diffusers) — carregado uma vez por worker; FlashBoot preserva o processo
# ---------------------------------------------------------------------------

class WanEngine:
    """Envolve o WanPipeline: codifica todos os prompts do job de uma vez e gera planos."""

    def __init__(self, pipe: Any, text_pipe: Any, text_encoder: Any, device: str, offload: str,
                 two_experts: bool, base_scheduler_config: Any, info: Dict[str, Any]) -> None:
        self.pipe = pipe
        self.text_pipe = text_pipe
        self.text_encoder = text_encoder
        self.device = device
        self.offload = offload
        self.two_experts = two_experts
        self.base_scheduler_config = base_scheduler_config
        self.flow_shift = float(base_scheduler_config["flow_shift"])
        self.vae_tiling = False
        self.info = info

    # -- texto -------------------------------------------------------------
    def encode(self, prompts: List[str], negative: Optional[str]) -> Dict[str, Any]:
        import torch  # noqa: WPS433

        on_demand = self.offload in ("t5", "model") and self.device.startswith("cuda")
        if on_demand:
            self.text_encoder.to(self.device)
        try:
            with torch.no_grad():
                pos, _ = self.text_pipe.encode_prompt(
                    prompt=list(prompts), do_classifier_free_guidance=False,
                    max_sequence_length=TEXT_LEN, device=self.device, dtype=torch.bfloat16)
                neg = None
                if negative is not None:
                    neg, _ = self.text_pipe.encode_prompt(
                        prompt=[negative], do_classifier_free_guidance=False,
                        max_sequence_length=TEXT_LEN, device=self.device, dtype=torch.bfloat16)
        finally:
            if on_demand:
                self.text_encoder.to("cpu")
                torch.cuda.empty_cache()
        return {"pos": pos, "neg": neg}

    # -- ajustes por job ---------------------------------------------------------
    def set_flow_shift(self, shift: float) -> None:
        if abs(shift - self.flow_shift) < 1e-9:
            return
        from diffusers import UniPCMultistepScheduler  # noqa: WPS433

        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.base_scheduler_config, flow_shift=shift)
        self.flow_shift = float(shift)

    def set_vae_tiling(self, enabled: bool) -> None:
        if enabled == self.vae_tiling:
            return
        if enabled:
            self.pipe.vae.enable_tiling()
        else:
            self.pipe.vae.disable_tiling()
        self.vae_tiling = enabled

    # -- geração de um plano ---------------------------------------------------
    def generate(self, embeds: Dict[str, Any], index: int, *, height: int, width: int,
                 num_frames: int, steps: int, cfg_scale: float, cfg_scale_2: Optional[float],
                 seed: int, on_step: Optional[Callable[[int, int], None]] = None) -> Any:
        import numpy as np  # noqa: WPS433
        import torch  # noqa: WPS433

        def _callback(pipe: Any, i: int, t: Any, callback_kwargs: Dict[str, Any]) -> Dict[str, Any]:
            if on_step is not None:
                on_step(i + 1, steps)
            return callback_kwargs

        kwargs: Dict[str, Any] = dict(
            prompt_embeds=embeds["pos"][index:index + 1],
            negative_prompt_embeds=embeds["neg"] if cfg_scale > 1.0 else None,
            height=height, width=width, num_frames=num_frames,
            num_inference_steps=steps, guidance_scale=cfg_scale,
            # gerador na CPU: o mesmo seed dá o mesmo ruído em qualquer GPU
            generator=torch.Generator(device="cpu").manual_seed(int(seed)),
            output_type="np", callback_on_step_end=_callback,
            callback_on_step_end_tensor_inputs=["latents"],
        )
        if self.two_experts:
            kwargs["guidance_scale_2"] = cfg_scale_2
        video = self.pipe(**kwargs).frames[0]  # (F, H, W, 3) float32 em [0, 1]
        video = np.asarray(video)
        return (np.clip(video, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def _load_engine() -> WanEngine:
    """Carrega tokenizer, T5, transformer(s), VAE e scheduler do volume (sem rede)."""
    import torch  # noqa: WPS433 - import pesado só no worker
    import diffusers  # noqa: WPS433
    from diffusers import AutoencoderKLWan, UniPCMultistepScheduler, WanPipeline, WanTransformer3DModel
    from transformers import AutoTokenizer, UMT5EncoderModel

    path = resolve_model_dir()
    with open(os.path.join(path, "model_index.json")) as fh:
        index = json.load(fh)
    if DEVICE.startswith("cuda"):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA indisponível neste worker")
        props = torch.cuda.get_device_properties(0)
        vram_gb, gpu = props.total_memory / 1e9, props.name
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    else:
        vram_gb, gpu = 0.0, DEVICE
        log.warning("rodando em %s: só para testes", DEVICE)
    mode = choose_offload(VARIANT, vram_gb)
    ram_gb = available_ram_gb()
    need_ram = MIN_RAM_OVERRIDE if MIN_RAM_OVERRIDE is not None else RESOURCES[(VARIANT, mode)]["ram"]
    log.info("GPU=%s VRAM=%.1fGB RAM=%.1fGB variante=%s modo=%s revisão=%s",
             gpu, vram_gb, ram_gb, VARIANT, mode, SPEC["revision"])
    if DEVICE.startswith("cuda") and ram_gb and ram_gb < need_ram:
        raise RuntimeError(
            f"RAM do worker {ram_gb:.0f} GB < {need_ram:.0f} GB necessários no modo {mode} "
            "(escolha uma GPU com mais VRAM para não precisar de offload)"
        )
    if not ready_marker_ok(path):
        log.warning("marcador .cineforge_ready ausente ou de outra revisão em %s", path)

    on_gpu = DEVICE.startswith("cuda")
    resident_map = DEVICE if (on_gpu and mode in ("none", "t5")) else None
    t5_map = DEVICE if (on_gpu and mode == "none") else None
    common = {"local_files_only": True}

    tokenizer = AutoTokenizer.from_pretrained(path, subfolder="tokenizer", **common)
    text_encoder = UMT5EncoderModel.from_pretrained(
        path, subfolder="text_encoder", torch_dtype=torch.bfloat16, device_map=t5_map, **common)
    transformer = WanTransformer3DModel.from_pretrained(
        path, subfolder="transformer", torch_dtype=torch.bfloat16, device_map=resident_map, **common)
    transformer_2 = None
    if SPEC["two_experts"]:
        transformer_2 = WanTransformer3DModel.from_pretrained(
            path, subfolder="transformer_2", torch_dtype=torch.bfloat16, device_map=resident_map, **common)
    # VAE em FP32, como no exemplo oficial do model card.
    vae = AutoencoderKLWan.from_pretrained(
        path, subfolder="vae", torch_dtype=torch.float32, device_map=resident_map, **common)
    base_scheduler = UniPCMultistepScheduler.from_pretrained(path, subfolder="scheduler", **common)
    shift = flow_shift_default(SPEC)
    scheduler = UniPCMultistepScheduler.from_config(base_scheduler.config, flow_shift=shift)

    pipe = WanPipeline(
        tokenizer=None, text_encoder=None, vae=vae, scheduler=scheduler,
        transformer=transformer, transformer_2=transformer_2,
        boundary_ratio=index.get("boundary_ratio"),
        expand_timesteps=bool(index.get("expand_timesteps", False)),
    )
    text_pipe = WanPipeline(tokenizer=tokenizer, text_encoder=text_encoder, vae=None,
                            scheduler=scheduler, transformer=None, transformer_2=None)
    if mode == "model":
        pipe.enable_model_cpu_offload(device=DEVICE)
    elif not on_gpu:
        pipe.to(DEVICE)
        text_encoder.to(DEVICE)
    pipe.set_progress_bar_config(disable=True)

    info = {"variant": VARIANT, "repo": SPEC["repo"], "revision": SPEC["revision"],
            "offload": mode, "gpu": gpu, "vram_gb": round(vram_gb, 1), "ram_gb": round(ram_gb, 1),
            "torch": torch.__version__, "diffusers": diffusers.__version__,
            "boundary_ratio": index.get("boundary_ratio")}
    engine = WanEngine(pipe, text_pipe, text_encoder, DEVICE, mode, SPEC["two_experts"],
                       base_scheduler.config, info)
    engine.flow_shift = shift
    return engine


# Ganchos substituíveis nos testes.
PIPELINE_FACTORY: Callable[[], Any] = _load_engine

_ENGINE = None
_ENGINE_LOCK = threading.Lock()
_TOKENIZER = None
_TOKENIZER_FAILED = False


def get_engine() -> Tuple[Any, float]:
    """Devolve (motor, segundos gastos carregando nesta chamada)."""
    global _ENGINE
    with _ENGINE_LOCK:
        if _ENGINE is not None:
            return _ENGINE, 0.0
        t0 = time.monotonic()
        _ENGINE = PIPELINE_FACTORY()
        load_s = time.monotonic() - t0
        log.info("modelo carregado em %.1fs", load_s)
        return _ENGINE, load_s


def _load_tokenizer() -> Any:
    from transformers import AutoTokenizer  # noqa: WPS433

    return AutoTokenizer.from_pretrained(model_dir(), subfolder="tokenizer", local_files_only=True)


TOKENIZER_FACTORY: Callable[[], Any] = _load_tokenizer


def prompt_clean(text: str) -> str:
    """Mesma limpeza do WanPipeline (ftfy + html.unescape duplo + espaços)."""
    try:
        import ftfy  # noqa: WPS433

        text = ftfy.fix_text(text)
    except ImportError:
        pass
    text = html.unescape(html.unescape(text)).strip()
    return _collapse(text)


def count_prompt_tokens(prompt: str) -> Tuple[int, bool]:
    """(tokens, exato?). Usa o tokenizer umT5 do volume; sem ele, estima."""
    global _TOKENIZER, _TOKENIZER_FAILED
    if _TOKENIZER is None and not _TOKENIZER_FAILED:
        try:
            _TOKENIZER = TOKENIZER_FACTORY()
        except Exception as exc:  # tokenizer ausente não pode derrubar o job
            _TOKENIZER_FAILED = True
            log.warning("tokenizer indisponível (%s); usando estimativa", exc)
    if _TOKENIZER is not None:
        return len(_TOKENIZER(prompt_clean(prompt), add_special_tokens=True)["input_ids"]), True
    return int(len(prompt.split()) * 1.3 + 20), False


def probe_vram_gb() -> float:
    """VRAM da GPU 0 em GB decimais sem carregar pesos (0 = desconhecida/sem CUDA)."""
    if _ENGINE is not None:
        return float(getattr(_ENGINE, "info", {}).get("vram_gb", 0) or 0)
    if not DEVICE.startswith("cuda"):
        return 0.0
    try:
        import torch  # noqa: WPS433

        if torch.cuda.is_available():
            return torch.cuda.get_device_properties(0).total_memory / 1e9
    except Exception:
        pass
    return 0.0


VRAM_PROBE: Callable[[], float] = probe_vram_gb


def want_vae_tiling(plan: Dict[str, Any], engine: Any) -> bool:
    if VAE_TILING in ("1", "true", "on", "sim", "yes"):
        return True
    if VAE_TILING in ("0", "false", "off", "nao", "não", "no"):
        return False
    vram = float(getattr(engine, "info", {}).get("vram_gb", 0) or 0)
    if not str(getattr(engine, "device", DEVICE)).startswith("cuda"):
        return False
    big_a14b = SPEC["two_experts"] and plan["height"] * plan["width"] > 480 * 832
    return bool(big_a14b or vram < 60)  # 48 GiB = ~51,5 GB decimais


# ---------------------------------------------------------------------------
# Vídeo: codificação, tamanho, upload presigned
# ---------------------------------------------------------------------------

def encode_mp4(frames: Any, fps: int, crf: int, out_path: str) -> int:
    """Um único H.264 yuv420p com faststart para todos os planos; devolve o tamanho."""
    import imageio  # noqa: WPS433
    import numpy as np  # noqa: WPS433

    writer = imageio.get_writer(
        out_path,
        format="FFMPEG",
        fps=fps,
        codec="libx264",
        quality=None,
        pixelformat="yuv420p",
        macro_block_size=16,
        ffmpeg_log_level="error",
        ffmpeg_params=["-crf", str(crf), "-preset", "medium", "-movflags", "+faststart"],
    )
    try:
        for frame in frames:
            writer.append_data(np.asarray(frame))
    finally:
        writer.close()
    return os.path.getsize(out_path)


ENCODER: Callable[[Any, int, int, str], int] = encode_mp4


def b64_len(n_bytes: int) -> int:
    return 4 * ((n_bytes + 2) // 3)


def crf_ladder(start: int) -> List[int]:
    ladder = [start]
    for step in (4, 8):  # no máximo 2 recodificações extras
        if start + step <= 40:
            ladder.append(start + step)
    return ladder


def http_put(url: str, data: bytes, content_type: str, attempts: int = 3) -> int:
    host = urllib.parse.urlsplit(url).hostname
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        req = urllib.request.Request(url, data=data, method="PUT",
                                     headers={"Content-Type": content_type})
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:  # noqa: S310 - https validado
                status = resp.status
            if 200 <= status < 300:
                log.info("upload presigned OK (%s, %d bytes)", host, len(data))
                return status
            last_exc = RuntimeError(f"upload devolveu HTTP {status}")
        except Exception as exc:  # rede instável: tenta de novo
            last_exc = exc
        log.warning("upload para %s falhou (tentativa %d/%d): %s", host, i + 1, attempts, last_exc)
        if i + 1 < attempts:
            time.sleep(2 ** i)
    raise RuntimeError(f"upload presigned falhou: {last_exc}")


# ---------------------------------------------------------------------------
# Progresso
# ---------------------------------------------------------------------------

def _progress(job: Dict[str, Any], message: str) -> None:
    if runpod is None:
        return
    try:
        runpod.serverless.progress_update(job, message)
    except Exception:  # progresso nunca derruba o job
        pass


def _step_reporter(job: Dict[str, Any], shot_no: int, total_shots: int, every: int = 5) -> Callable[[int, int], None]:
    t0 = time.monotonic()

    def report(step: int, total: int) -> None:
        if step == 1 or step % every == 0 or step == total:
            rate = (time.monotonic() - t0) / step
            eta = rate * (total - step) / 60
            _progress(job, f"plano {shot_no}/{total_shots}: passo {step}/{total}, ~{eta:.0f} min p/ este plano")

    return report


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    import numpy as np  # noqa: WPS433

    t_start = time.monotonic()
    job_id = job.get("id", "local")
    try:
        plan = validate_and_build(job.get("input"))
    except InputError as exc:
        log.info("job %s rejeitado: %s", job_id, exc)
        return {"error": f"entrada inválida: {exc}"}

    exact_all = True
    for sp in plan["shots"]:
        tokens, exact = count_prompt_tokens(sp["prompt"])
        sp["prompt_tokens"] = tokens
        exact_all = exact_all and exact
        if tokens > MAX_PROMPT_TOKENS:
            msg = (f"prompt do plano {sp['index'] + 1} com {tokens} tokens "
                   f"{'(exato)' if exact else '(estimado)'} > {MAX_PROMPT_TOKENS}; o T5 corta o excesso")
            if exact and not plan["allow_prompt_truncation"]:
                return {"error": f"entrada inválida: {msg}. Encurte a global caption ou a caption do plano."}
            plan["warnings"].append(msg)
    log.info("job %s: modo=%s planos=%d frames=%d passos=%d cortes=%s",
             job_id, plan["mode"], plan["num_shots"], plan["num_frames"],
             plan["num_inference_steps"], plan["shot_cut_frames"])

    workdir = tempfile.mkdtemp(prefix="wan22-")
    clips: List[Any] = []
    try:
        if SPEC["two_experts"] and plan["height"] * plan["width"] > 480 * 832:
            vram = VRAM_PROBE()  # sem carregar o modelo: só consulta a GPU
            if 0 < vram < 75:
                return {"error": "entrada inválida: 720P no A14B exige GPU de 80 GB; use 480x832 ou troque a GPU"}
        _progress(job, "carregando modelo" if _ENGINE is None else "modelo em memória")
        engine, load_s = get_engine()
        info = getattr(engine, "info", {})
        engine.set_flow_shift(plan["flow_shift"])
        engine.set_vae_tiling(want_vae_tiling(plan, engine))

        _progress(job, "codificando prompts")
        t_text = time.monotonic()
        embeds = engine.encode([sp["prompt"] for sp in plan["shots"]],
                               plan["negative_prompt"] if plan["cfg_scale"] > 1.0 else None)
        text_s = time.monotonic() - t_text

        gen_total = 0.0
        for sp in plan["shots"]:
            shot_no = sp["index"] + 1
            _progress(job, f"gerando plano {shot_no}/{plan['num_shots']}")
            t_shot = time.monotonic()
            video = engine.generate(
                embeds, sp["index"], height=plan["height"], width=plan["width"],
                num_frames=sp["frames_generated"], steps=plan["num_inference_steps"],
                cfg_scale=plan["cfg_scale"], cfg_scale_2=plan["cfg_scale_2"], seed=sp["seed"],
                on_step=_step_reporter(job, shot_no, plan["num_shots"]),
            )
            video = np.asarray(video)
            if video.ndim != 4 or video.shape[0] < sp["frames_used"]:
                raise RuntimeError(f"plano {shot_no}: o pipeline devolveu {video.shape}, "
                                   f"esperado >= {sp['frames_used']} frames")
            if video.dtype != np.uint8:
                video = (np.clip(video, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
            clips.append(video[:sp["frames_used"]])
            sp["generation_s"] = round(time.monotonic() - t_shot, 1)
            gen_total += sp["generation_s"]
            log.info("job %s: plano %d/%d pronto em %.0fs", job_id, shot_no, plan["num_shots"], sp["generation_s"])

        frames = np.concatenate(clips, axis=0)
        clips = []
        if frames.shape[0] != plan["num_frames"]:
            raise RuntimeError(f"vídeo com {frames.shape[0]} frames, esperado {plan['num_frames']}")

        _progress(job, "codificando mp4")
        t_enc = time.monotonic()
        out_path = os.path.join(workdir, plan["file_name"])
        ladder = [plan["crf"]] if (plan["upload_url"] or not plan["return_base64"]) else crf_ladder(plan["crf"])
        size = 0
        used_crf = plan["crf"]
        for used_crf in ladder:
            size = ENCODER(frames, plan["fps"], used_crf, out_path)
            if plan["upload_url"] or b64_len(size) <= MAX_INLINE_B64:
                break
            plan["warnings"].append(f"mp4 com {size} bytes não cabe inline; recodificando com crf>{used_crf}")
        encode_s = time.monotonic() - t_enc
        with open(out_path, "rb") as fh:
            data = fh.read()

        shots_meta = [{
            "shot": sp["index"] + 1, "start_frame": sp["start_frame"], "frames_used": sp["frames_used"],
            "frames_generated": sp["frames_generated"], "seed": sp["seed"],
            "prompt_tokens": sp["prompt_tokens"], "generation_s": sp["generation_s"],
        } for sp in plan["shots"]]
        result: Dict[str, Any] = {
            "mime_type": "video/mp4",
            "file_name": plan["file_name"],
            "output_path": plan["output_rel"],
            "frames": int(frames.shape[0]),
            "fps": plan["fps"],
            "seconds": round(frames.shape[0] / plan["fps"], 2),
            "width": plan["width"],
            "height": plan["height"],
            "num_shots": plan["num_shots"],
            "shot_cut_frames": plan["shot_cut_frames"],
            "shots": shots_meta,
            "seed": plan["seed"],
            "num_inference_steps": plan["num_inference_steps"],
            "cfg_scale": plan["cfg_scale"],
            "cfg_scale_2": plan["cfg_scale_2"],
            "flow_shift": plan["flow_shift"],
            "vae_tiling": bool(getattr(engine, "vae_tiling", False)),
            "crf": used_crf,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "prompt_tokens": max(sp["prompt_tokens"] for sp in plan["shots"]),
            "prompt_tokens_exact": exact_all,
            "model_load_s": round(load_s, 1),
            "text_encode_s": round(text_s, 1),
            "generation_s": round(gen_total, 1),
            "encode_s": round(encode_s, 1),
            "worker": dict(info),
            "uploaded": False,
        }
        frames = None

        if plan["upload_url"]:
            _progress(job, "enviando para URL presigned")
            http_put(plan["upload_url"], data, plan["upload_content_type"])
            result["uploaded"] = True

        if plan["return_base64"]:
            if b64_len(len(data)) > MAX_INLINE_B64 and not plan["upload_url"]:
                return {"error": (
                    f"vídeo final com {len(data)} bytes não cabe no limite de 10 MB do /run "
                    "mesmo com crf alto; reduza num_frames ou envie output_upload_url (presigned PUT)"
                )}
            if b64_len(len(data)) <= MAX_INLINE_B64:
                result["video_b64"] = base64.b64encode(data).decode("ascii")
            else:
                plan["warnings"].append("vídeo grande demais para inline; use a cópia enviada à URL presigned")

        if SAVE_OUTPUTS and plan["output_rel"]:
            dest = os.path.join(OUTPUT_DIR, plan["output_rel"])
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(out_path, dest)
            result["volume_path"] = dest

        result["warnings"] = plan["warnings"]
        result["elapsed_s"] = round(time.monotonic() - t_start, 1)
        log.info("job %s concluído: %d frames, %d bytes, crf=%d, %.0fs",
                 job_id, result["frames"], len(data), used_crf, result["elapsed_s"])
        return result

    except Exception as exc:
        log.error("job %s falhou: %s\n%s", job_id, exc, traceback.format_exc())
        text = f"{type(exc).__name__}: {exc}"
        out: Dict[str, Any] = {"error": text[:2000]}
        if "OutOfMemoryError" in type(exc).__name__ or "out of memory" in str(exc).lower():
            out["error"] = (f"{text[:1500]} — sem VRAM; reduza a resolução (480x832), "
                            "os frames por plano, ou use GPU maior")
        elif "CUDA error" in str(exc) or "device-side assert" in str(exc):
            out["refresh_worker"] = True  # contexto CUDA corrompido: recicla o worker
        return out
    finally:
        clips = []
        shutil.rmtree(workdir, ignore_errors=True)
        gc.collect()
        try:
            import torch  # noqa: WPS433

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


if __name__ == "__main__":
    if runpod is None:
        raise SystemExit("SDK runpod ausente: instale requirements.txt")
    if VARIANT not in VARIANTS:
        raise SystemExit(f"MODEL_VARIANT inválido: {VARIANT!r} (use a14b ou ti2v-5b)")
    if EAGER_LOAD:  # exige RUNPOD_INIT_TIMEOUT alto no endpoint
        get_engine()
    runpod.serverless.start({"handler": handler})
