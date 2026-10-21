"""
FastAPI wrapper around WanGP for the RunPod persistent pod.

Exposto em :8080/generate
O CineForge chama: POST https://{pod_id}-8080.proxy.runpod.net/generate

Segurança:
  - Recebe apenas prompt + parâmetros de geração (sem credenciais).
  - Credenciais do pod são injetadas via variáveis de ambiente pelo RunPod.
  - Nunca lê .env ou arquivos de configuração locais.
"""

import logging
import os
import sys
import tempfile
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

log = logging.getLogger("wan22_server")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ---------------------------------------------------------------------------
# WanGP pipeline (carregado uma vez no startup para zero cold start)
# ---------------------------------------------------------------------------
_pipeline = None

def _load_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    wangp_path = Path(os.environ.get("WANGP_PATH", "/workspace/WanGP"))
    if not wangp_path.exists():
        raise RuntimeError(f"WanGP não encontrado em {wangp_path}")

    sys.path.insert(0, str(wangp_path))

    # Import lazy para evitar falha no startup se CUDA não disponível
    try:
        from wan.pipeline import WanPipeline  # type: ignore
        model_path = os.environ.get("WAN22_MODEL_PATH", "/workspace/models/wan2.2")
        log.info("Carregando Wan2.2 de %s …", model_path)
        _pipeline = WanPipeline.from_pretrained(model_path)
        _pipeline.to("cuda")
        log.info("Wan2.2 carregado e pronto.")
    except Exception as exc:
        log.error("Falha ao carregar Wan2.2: %s", exc)
        raise

    return _pipeline


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="", max_length=1000)
    duration_seconds: float = Field(default=5.0, ge=1.0, le=30.0)
    width: int = Field(default=1280, ge=256, le=1920)
    height: int = Field(default=720, ge=256, le=1080)
    num_inference_steps: int = Field(default=30, ge=10, le=60)
    guidance_scale: float = Field(default=7.5, ge=1.0, le=20.0)
    seed: int = Field(default=-1)  # -1 = aleatório


class GenerateResponse(BaseModel):
    video_id: str
    duration_seconds: float
    width: int
    height: int
    download_path: str  # path relativo para /video/{video_id}


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="CineForge Wan2.2 Pod", version="1.0.0")

# Pasta temporária para vídeos gerados (limpeza periódica via cron externo)
_OUTPUT_DIR = Path(os.environ.get("WAN22_OUTPUT_DIR", "/tmp/wan22_outputs"))
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Pré-carrega o pipeline para zero cold start nas requisições."""
    try:
        _load_pipeline()
    except Exception as exc:
        log.warning("Pipeline não pré-carregado no startup: %s", exc)


@app.get("/health")
async def health():
    return {"status": "ok", "pipeline_loaded": _pipeline is not None}


@app.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    t0 = time.perf_counter()
    video_id = str(uuid.uuid4())

    try:
        pipeline = _load_pipeline()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Pipeline indisponível: {exc}")

    fps = 24
    num_frames = int(req.duration_seconds * fps)
    seed = req.seed if req.seed >= 0 else int(time.time() * 1000) % (2**31)

    log.info(
        "Gerando vídeo %s | prompt=%r | %dx%d | %.1fs | seed=%d",
        video_id, req.prompt[:80], req.width, req.height, req.duration_seconds, seed,
    )

    try:
        import torch
        generator = torch.Generator(device="cuda").manual_seed(seed)
        result = pipeline(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or None,
            num_frames=num_frames,
            height=req.height,
            width=req.width,
            num_inference_steps=req.num_inference_steps,
            guidance_scale=req.guidance_scale,
            generator=generator,
        )
    except Exception as exc:
        log.error("Falha na geração %s: %s", video_id, exc)
        raise HTTPException(status_code=500, detail=f"Falha na geração: {exc}")

    output_path = _OUTPUT_DIR / f"{video_id}.mp4"
    try:
        import imageio
        writer = imageio.get_writer(str(output_path), fps=fps, codec="libx264", quality=8)
        for frame in result.frames[0]:
            import numpy as np
            writer.append_data(np.array(frame))
        writer.close()
    except Exception as exc:
        log.error("Falha ao salvar vídeo %s: %s", video_id, exc)
        raise HTTPException(status_code=500, detail=f"Falha ao salvar vídeo: {exc}")

    elapsed = time.perf_counter() - t0
    log.info("Vídeo %s gerado em %.1fs", video_id, elapsed)

    return GenerateResponse(
        video_id=video_id,
        duration_seconds=req.duration_seconds,
        width=req.width,
        height=req.height,
        download_path=f"/video/{video_id}",
    )


@app.get("/video/{video_id}")
async def download_video(video_id: str):
    # Sanitiza o ID para evitar path traversal
    if not video_id.replace("-", "").isalnum() or len(video_id) > 64:
        raise HTTPException(status_code=400, detail="video_id inválido")

    path = _OUTPUT_DIR / f"{video_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    return FileResponse(str(path), media_type="video/mp4", filename=f"{video_id}.mp4")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
