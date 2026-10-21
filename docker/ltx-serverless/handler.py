"""
CineForge — RunPod Serverless Worker: LTX-Video

Ponto de entrada para o RunPod Serverless runtime.
O runtime chama handler(job) para cada requisição.

Segurança:
  - Recebe apenas prompt + parâmetros de geração (sem credenciais).
  - Credenciais de storage são injetadas via variáveis de ambiente pelo RunPod.
  - Retorna URL presigned S3/R2 para download (nunca base64 — muito pesado para vídeo).
  - Nunca lê .env ou arquivos de configuração locais.

Variáveis de ambiente esperadas (injetadas pelo RunPod):
  LTX_MODEL_ID      — repo HuggingFace ou caminho local do modelo LTX-Video
  AWS_BUCKET        — bucket S3/R2 para upload dos mp4 gerados
  AWS_REGION        — região S3 (padrão: auto para Cloudflare R2)
  AWS_ENDPOINT_URL  — endpoint R2 ou S3 compatível (opcional)
  AWS_ACCESS_KEY_ID     — credencial de acesso
  AWS_SECRET_ACCESS_KEY — credencial secreta
"""

import logging
import os
import time
import uuid
from pathlib import Path

import runpod

log = logging.getLogger("ltx_handler")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# Modelo LTX-Video (carregado uma vez, reutilizado entre jobs)
# ---------------------------------------------------------------------------
_pipe = None

_LTX_MODEL_ID = os.environ.get("LTX_MODEL_ID", "Lightricks/LTX-Video")
_OUTPUT_DIR = Path("/tmp/ltx_outputs")
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _load_pipe():
    global _pipe
    if _pipe is not None:
        return _pipe

    log.info("Carregando LTX-Video de %s …", _LTX_MODEL_ID)
    import torch
    from diffusers import LTXPipeline

    _pipe = LTXPipeline.from_pretrained(
        _LTX_MODEL_ID,
        torch_dtype=torch.bfloat16,
    )
    _pipe.to("cuda")
    log.info("LTX-Video carregado e pronto.")
    return _pipe


# ---------------------------------------------------------------------------
# Upload para S3 / Cloudflare R2
# ---------------------------------------------------------------------------

def _upload_to_s3(local_path: Path, object_key: str) -> str:
    """Faz upload do mp4 para S3/R2 e retorna URL presigned (1 hora de validade)."""
    import boto3

    kwargs = {
        "region_name": os.environ.get("AWS_REGION", "auto"),
    }
    endpoint = os.environ.get("AWS_ENDPOINT_URL")
    if endpoint:
        kwargs["endpoint_url"] = endpoint

    s3 = boto3.client("s3", **kwargs)
    bucket = os.environ["AWS_BUCKET"]

    s3.upload_file(
        str(local_path),
        bucket,
        object_key,
        ExtraArgs={"ContentType": "video/mp4"},
    )

    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=3600,
    )
    return url


# ---------------------------------------------------------------------------
# Handler principal
# ---------------------------------------------------------------------------

def handler(job: dict) -> dict:
    """
    Entrada do RunPod Serverless.

    Input esperado (job["input"]):
      prompt              str   — prompt de geração (obrigatório)
      negative_prompt     str   — prompt negativo (opcional)
      duration_seconds    float — duração em segundos (padrão: 5.0, max: 10.0)
      width               int   — largura em pixels (padrão: 1280)
      height              int   — altura em pixels (padrão: 720)
      num_inference_steps int   — steps de inferência (padrão: 30)
      guidance_scale      float — escala de orientação (padrão: 3.0)
      seed                int   — semente (-1 = aleatório)
      scene_id            int   — id da cena CineForge (para nomear o arquivo)

    Output retornado:
      download_url  str   — URL presigned S3/R2 para download do mp4
      video_id      str   — uuid do vídeo gerado
      duration_seconds float
      width         int
      height        int
      provider      str   — "runpod_ltx"
    """
    t0 = time.perf_counter()
    job_input = job.get("input", {})

    # --- Validação de entrada ---
    prompt = job_input.get("prompt", "").strip()
    if not prompt:
        return {"error": "Campo 'prompt' é obrigatório."}

    negative_prompt = job_input.get("negative_prompt", "")
    duration_seconds = float(job_input.get("duration_seconds", 5.0))
    duration_seconds = max(1.0, min(10.0, duration_seconds))
    width = int(job_input.get("width", 1280))
    height = int(job_input.get("height", 720))
    num_inference_steps = int(job_input.get("num_inference_steps", 30))
    guidance_scale = float(job_input.get("guidance_scale", 3.0))
    seed_input = int(job_input.get("seed", -1))
    scene_id = int(job_input.get("scene_id", 0))

    video_id = str(uuid.uuid4())
    seed = seed_input if seed_input >= 0 else int(time.time() * 1000) % (2**31)

    log.info(
        "Job %s | scene=%d | prompt=%r | %dx%d | %.1fs | seed=%d",
        video_id, scene_id, prompt[:80], width, height, duration_seconds, seed,
    )

    # --- Carregar modelo ---
    try:
        pipe = _load_pipe()
    except Exception as exc:
        log.error("Falha ao carregar LTX-Video: %s", exc)
        return {"error": f"Falha ao carregar modelo: {exc}"}

    # --- Inferência ---
    fps = 24
    num_frames = int(duration_seconds * fps)

    try:
        import torch
        generator = torch.Generator(device="cuda").manual_seed(seed)
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt or None,
            num_frames=num_frames,
            height=height,
            width=width,
            num_inference_steps=num_inference_steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )
    except Exception as exc:
        log.error("Falha na geração %s: %s", video_id, exc)
        return {"error": f"Falha na geração: {exc}"}

    # --- Salvar mp4 ---
    output_filename = f"scene{scene_id:03d}_{video_id}_runpod_ltx.mp4"
    output_path = _OUTPUT_DIR / output_filename

    try:
        import imageio
        import numpy as np

        writer = imageio.get_writer(
            str(output_path), fps=fps, codec="libx264", quality=8
        )
        for frame in result.frames[0]:
            writer.append_data(np.array(frame))
        writer.close()
    except Exception as exc:
        log.error("Falha ao salvar vídeo %s: %s", video_id, exc)
        return {"error": f"Falha ao salvar vídeo: {exc}"}

    # --- Upload para S3/R2 ---
    try:
        object_key = f"ltx/{output_filename}"
        download_url = _upload_to_s3(output_path, object_key)
    except Exception as exc:
        log.error("Falha no upload S3 para %s: %s", video_id, exc)
        return {"error": f"Falha no upload: {exc}"}
    finally:
        # Limpa o arquivo local após upload
        try:
            output_path.unlink(missing_ok=True)
        except Exception:
            pass

    elapsed = time.perf_counter() - t0
    log.info("Job %s concluído em %.1fs | url=%s", video_id, elapsed, download_url[:60])

    return {
        "download_url": download_url,
        "video_id": video_id,
        "duration_seconds": duration_seconds,
        "width": width,
        "height": height,
        "provider": "runpod_ltx",
        "elapsed_seconds": round(elapsed, 1),
    }


# ---------------------------------------------------------------------------
# Entrypoint RunPod Serverless
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Pré-carrega o modelo antes de aceitar jobs (reduz cold start)
    log.info("Pré-carregando LTX-Video …")
    try:
        _load_pipe()
        log.info("Pré-carga concluída. Aguardando jobs …")
    except Exception as exc:
        log.warning("Pré-carga falhou (será tentada no primeiro job): %s", exc)

    runpod.serverless.start({"handler": handler})
