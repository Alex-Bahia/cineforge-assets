"""
fal.ai Provider — aggregator de 600+ modelos de vídeo/imagem com custo reduzido.

Modelos suportados e custo estimado (outubro 2026):
  ltx-video-2.5-fast     → $0.04/seg (melhor custo-benefício, 1080p)
  ltx-video-2.5-pro      → $0.06/seg (alta qualidade)
  kling-v2.1-pro         → $0.084/seg (alternativa Kling via fal.ai)
  veo3                   → acesso exclusivo via fal.ai (~$0.40-0.60/seg)
  wan-2.1-t2v-720p       → $0.04/seg (open source, boa qualidade)
  stable-diffusion-3     → $0.003/imagem (thumbnails)

Vantagens vs. APIs diretas:
  - Endpoint único para múltiplos modelos
  - Cold start ~0 (serverless otimizado)
  - Fallback automático entre modelos
  - ~30-50% mais barato que APIs diretas para maioria dos modelos
"""
import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
import time

log = logging.getLogger(__name__)

FAL_API_BASE = "https://fal.run"
FAL_QUEUE_BASE = "https://queue.fal.run"


@dataclass
class FalModel:
    model_id: str
    cost_per_second: float
    max_duration: int = 10
    supports_audio: bool = False
    resolution: str = "720p"
    quality_tier: str = "standard"


FAL_MODELS: dict[str, FalModel] = {
    "ltx_fast": FalModel(
        model_id="fal-ai/ltx-video-v0-9-1",
        cost_per_second=0.04,
        max_duration=10,
        resolution="1080p",
        quality_tier="fast",
    ),
    "ltx_pro": FalModel(
        model_id="fal-ai/ltx-video",
        cost_per_second=0.06,
        max_duration=16,
        resolution="1080p",
        quality_tier="pro",
    ),
    "wan_720p": FalModel(
        model_id="fal-ai/wan-v2-1-13b-t2v",
        cost_per_second=0.04,
        max_duration=10,
        resolution="720p",
        quality_tier="standard",
    ),
    "kling_pro": FalModel(
        model_id="fal-ai/kling-video/v2.1/pro/text-to-video",
        cost_per_second=0.084,
        max_duration=10,
        resolution="720p",
        quality_tier="premium",
    ),
    "veo3": FalModel(
        model_id="fal-ai/veo3",
        cost_per_second=0.50,
        max_duration=8,
        supports_audio=True,
        resolution="1080p",
        quality_tier="ultra",
    ),
}

NICHE_MODEL_PREFERENCE = {
    "finance_dark": ["ltx_pro", "kling_pro", "ltx_fast"],
    "dark": ["ltx_pro", "wan_720p", "ltx_fast"],
    "kids": ["wan_720p", "ltx_fast", "ltx_pro"],
    "tech": ["ltx_fast", "wan_720p", "ltx_pro"],
    "education": ["ltx_fast", "wan_720p", "ltx_pro"],
}


class FalProvider:
    """
    Provedor unificado fal.ai — acessa LTX, Wan, Kling, Veo3 via endpoint único.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FAL_KEY") or os.getenv("FAL_API_KEY")
        self._available = bool(self.api_key)
        if not self._available:
            log.warning("FalProvider: FAL_KEY não configurada — provedor desabilitado")

    def is_available(self) -> bool:
        return self._available

    def _headers(self) -> dict:
        return {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }

    def cost_per_second(self, model_key: str = "ltx_fast") -> float:
        return FAL_MODELS.get(model_key, FAL_MODELS["ltx_fast"]).cost_per_second

    def select_model(self, niche: str = "dark", quality: str = "auto") -> str:
        """Seleciona o modelo mais adequado para o nicho e qualidade desejada."""
        if quality == "ultra":
            return "veo3"
        if quality == "premium":
            return "kling_pro"
        prefs = NICHE_MODEL_PREFERENCE.get(niche, NICHE_MODEL_PREFERENCE["dark"])
        return prefs[0]

    async def generate_video_async(
        self,
        prompt: str,
        model_key: str = "ltx_fast",
        duration_seconds: int = 5,
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
        negative_prompt: str = "blurry, low quality, watermark, text overlay, logo",
    ) -> Optional[Path]:
        """
        Gera vídeo via fal.ai de forma assíncrona com polling de status.
        """
        if not self._available:
            return None

        model = FAL_MODELS.get(model_key, FAL_MODELS["ltx_fast"])
        duration = min(duration_seconds, model.max_duration)

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_frames": duration * 24,
            "fps": 24,
            "width": 1280 if "1080" in model.resolution else 1280,
            "height": 720 if "720" in model.resolution else 720,
        }

        log.info(
            "FalProvider: gerando scene %d via %s (%s, $%.3f/s)",
            scene_id, model.model_id, model.quality_tier,
            model.cost_per_second,
        )

        try:
            import urllib.request
            import urllib.error

            # Submit job to queue
            queue_url = f"{FAL_QUEUE_BASE}/{model.model_id}"
            req_data = json.dumps(payload).encode()
            req = urllib.request.Request(
                queue_url, data=req_data,
                headers=self._headers(), method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                job = json.loads(resp.read())

            request_id = job.get("request_id")
            if not request_id:
                log.error("FalProvider: sem request_id na resposta")
                return None

            # Poll for completion
            status_url = f"{FAL_QUEUE_BASE}/{model.model_id}/requests/{request_id}/status"
            result_url = f"{FAL_QUEUE_BASE}/{model.model_id}/requests/{request_id}"

            for attempt in range(60):  # max 5 min with 5s intervals
                await asyncio.sleep(5)

                status_req = urllib.request.Request(
                    status_url, headers=self._headers()
                )
                with urllib.request.urlopen(status_req, timeout=15) as sr:
                    status = json.loads(sr.read())

                state = status.get("status", "")
                if state == "COMPLETED":
                    break
                elif state in ("FAILED", "CANCELLED"):
                    log.error("FalProvider: job %s falhou: %s", request_id, state)
                    return None

                if attempt % 6 == 0:
                    log.debug("FalProvider: aguardando scene %d... (%ds)", scene_id, attempt * 5)

            # Fetch result
            result_req = urllib.request.Request(result_url, headers=self._headers())
            with urllib.request.urlopen(result_req, timeout=30) as rr:
                result = json.loads(rr.read())

            video_url = None
            if "video" in result:
                video_url = result["video"].get("url") or result["video"]
            elif "videos" in result and result["videos"]:
                video_url = result["videos"][0].get("url")

            if not video_url:
                log.error("FalProvider: sem URL de vídeo na resposta")
                return None

            # Download video
            if output_dir is None:
                output_dir = Path("batch/videos")
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f"{video_id}_scene{scene_id:03d}_fal_{model_key}.mp4"

            dl_req = urllib.request.Request(video_url)
            with urllib.request.urlopen(dl_req, timeout=120) as vr:
                out_path.write_bytes(vr.read())

            log.info(
                "FalProvider: scene %d concluída → %s (custo ~$%.3f)",
                scene_id, out_path.name, duration * model.cost_per_second,
            )
            return out_path

        except Exception as exc:
            log.error("FalProvider: erro ao gerar scene %d: %s", scene_id, exc)
            return None

    def generate_video(
        self,
        prompt: str,
        model_key: str = "ltx_fast",
        duration_seconds: int = 5,
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Wrapper síncrono em torno do método async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.generate_video_async(
                            prompt=prompt,
                            model_key=model_key,
                            duration_seconds=duration_seconds,
                            scene_id=scene_id,
                            video_id=video_id,
                            output_dir=output_dir,
                        )
                    )
                    return future.result(timeout=600)
            else:
                return loop.run_until_complete(
                    self.generate_video_async(
                        prompt=prompt,
                        model_key=model_key,
                        duration_seconds=duration_seconds,
                        scene_id=scene_id,
                        video_id=video_id,
                        output_dir=output_dir,
                    )
                )
        except Exception as exc:
            log.error("FalProvider: generate_video sync wrapper falhou: %s", exc)
            return None

    def generate_thumbnail(
        self,
        prompt: str,
        output_dir: Optional[Path] = None,
        video_id: str = "",
        scene_id: int = 0,
    ) -> Optional[Path]:
        """Gera thumbnail via fal.ai Stable Diffusion 3 ($0.003/imagem)."""
        if not self._available:
            return None

        try:
            import urllib.request
            import urllib.error

            payload = {
                "prompt": prompt,
                "negative_prompt": "blurry, text, watermark, logo, low quality",
                "image_size": "landscape_16_9",
                "num_inference_steps": 28,
                "guidance_scale": 7.5,
            }

            req_data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{FAL_API_BASE}/fal-ai/stable-diffusion-v3-medium",
                data=req_data,
                headers=self._headers(),
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())

            img_url = result.get("images", [{}])[0].get("url")
            if not img_url:
                return None

            if output_dir is None:
                output_dir = Path("batch/thumbnails")
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f"{video_id}_thumb_fal.jpg"

            dl_req = urllib.request.Request(img_url)
            with urllib.request.urlopen(dl_req, timeout=30) as ir:
                out_path.write_bytes(ir.read())

            log.info("FalProvider: thumbnail gerada → %s", out_path.name)
            return out_path

        except Exception as exc:
            log.error("FalProvider: erro ao gerar thumbnail: %s", exc)
            return None


_fal_provider: Optional[FalProvider] = None


def get_fal_provider() -> FalProvider:
    global _fal_provider
    if _fal_provider is None:
        _fal_provider = FalProvider()
    return _fal_provider
