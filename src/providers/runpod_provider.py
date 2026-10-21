"""
RunPod Provider — integração dual-mode: Serverless (LTX-Video) + Pod Persistente (Wan2.2/WanGP).

Modo 1 — RunPod Serverless (LTX-Video):
  - Endpoint serverless: POST https://api.runpod.ai/v2/{endpoint_id}/run
  - Cold start: 45–90s (aceitável para geração em volume)
  - Custo estimado: ~$0.02–0.04/seg no hardware alugado
  - Uso: cenas padrão/bulk, alternativa econômica ao fal.ai LTX

Modo 2 — RunPod Pod Persistente (Wan2.2 via WanGP):
  - Pod sempre ativo: POST https://{pod_id}-8080.proxy.runpod.net/generate
  - Cold start: zero (pod rodando continuamente)
  - Motor: deepbeepmeep/WanGP (fork otimizado do Wan2.1)
  - Uso: cenas hero/cinemáticas, onde zero cold start é crítico

Variáveis de ambiente necessárias:
  RUNPOD_API_KEY           → chave de API RunPod (modo serverless)
  RUNPOD_LTX_ENDPOINT_ID  → ID do endpoint serverless LTX-Video
  RUNPOD_WAN22_POD_URL     → URL base do pod persistente, ex:
                             https://{pod_id}-8080.proxy.runpod.net
"""
import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

RUNPOD_API_BASE = "https://api.runpod.ai/v2"

# Polling config para serverless
_SERVERLESS_POLL_INTERVAL = 5   # segundos entre polls
_SERVERLESS_MAX_POLLS = 120     # max 10 min (120 × 5s)

# Timeout para pod persistente (já está quente, resposta direta)
_POD_REQUEST_TIMEOUT = 300      # 5 min para geração


class RunPodProvider:
    """
    Provedor RunPod — suporta geração via serverless (LTX) e pod persistente (Wan2.2).

    Não lança exceções no __init__: disponibilidade verificada pelos métodos
    is_ltx_available() e is_wan22_available(), que testam as env vars necessárias.
    """

    def __init__(self):
        self.api_key = os.getenv("RUNPOD_API_KEY")
        self.ltx_endpoint_id = os.getenv("RUNPOD_LTX_ENDPOINT_ID")
        # URL base do pod: https://{pod_id}-8080.proxy.runpod.net
        self.wan22_pod_url = os.getenv("RUNPOD_WAN22_POD_URL", "").rstrip("/")

        if not self.api_key:
            log.debug("RunPodProvider: RUNPOD_API_KEY ausente — serverless desabilitado")
        if not self.ltx_endpoint_id:
            log.debug("RunPodProvider: RUNPOD_LTX_ENDPOINT_ID ausente — LTX serverless desabilitado")
        if not self.wan22_pod_url:
            log.debug("RunPodProvider: RUNPOD_WAN22_POD_URL ausente — pod persistente desabilitado")

    # ------------------------------------------------------------------ #
    # Disponibilidade                                                       #
    # ------------------------------------------------------------------ #

    def is_ltx_available(self) -> bool:
        """True se as credenciais para LTX serverless estão configuradas."""
        return bool(self.api_key and self.ltx_endpoint_id)

    def is_wan22_available(self) -> bool:
        """True se a URL do pod persistente Wan2.2 está configurada."""
        return bool(self.wan22_pod_url)

    # ------------------------------------------------------------------ #
    # Headers                                                               #
    # ------------------------------------------------------------------ #

    def _runpod_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _pod_headers(self) -> dict:
        return {"Content-Type": "application/json"}

    # ------------------------------------------------------------------ #
    # Modo 1 — LTX-Video via RunPod Serverless                             #
    # ------------------------------------------------------------------ #

    async def generate_ltx_serverless_async(
        self,
        prompt: str,
        duration_seconds: int = 5,
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
        negative_prompt: str = "blurry, low quality, watermark, text overlay, logo",
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
    ) -> Optional[Path]:
        """
        Gera vídeo via LTX-Video no endpoint serverless RunPod.

        Fluxo:
          1. POST /v2/{endpoint_id}/run  → recebe job_id
          2. Poll GET /v2/{endpoint_id}/status/{job_id} até COMPLETED/FAILED
          3. Baixa o vídeo da URL retornada no output
        """
        if not self.is_ltx_available():
            log.warning("RunPodProvider: LTX serverless não disponível — env vars ausentes")
            return None

        import urllib.request
        import urllib.error

        payload = {
            "input": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_frames": duration_seconds * fps,
                "fps": fps,
                "width": width,
                "height": height,
                "num_inference_steps": 30,
                "guidance_scale": 3.5,
            }
        }

        submit_url = f"{RUNPOD_API_BASE}/{self.ltx_endpoint_id}/run"
        log.info(
            "RunPodProvider: submetendo LTX serverless scene %d → %s",
            scene_id, submit_url
        )

        try:
            # --- Passo 1: submissão do job ---
            req_data = json.dumps(payload).encode()
            req = urllib.request.Request(
                submit_url, data=req_data,
                headers=self._runpod_headers(), method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                job = json.loads(resp.read())

            job_id = job.get("id")
            if not job_id:
                log.error("RunPodProvider: resposta sem job id: %s", job)
                return None

            log.info("RunPodProvider: LTX job %s criado (scene %d)", job_id, scene_id)

            # --- Passo 2: polling de status ---
            status_url = f"{RUNPOD_API_BASE}/{self.ltx_endpoint_id}/status/{job_id}"

            for attempt in range(_SERVERLESS_MAX_POLLS):
                await asyncio.sleep(_SERVERLESS_POLL_INTERVAL)

                status_req = urllib.request.Request(
                    status_url, headers=self._runpod_headers()
                )
                with urllib.request.urlopen(status_req, timeout=15) as sr:
                    status = json.loads(sr.read())

                state = status.get("status", "")

                if state == "COMPLETED":
                    log.info(
                        "RunPodProvider: LTX job %s COMPLETED após %ds",
                        job_id, (attempt + 1) * _SERVERLESS_POLL_INTERVAL
                    )
                    break
                elif state in ("FAILED", "CANCELLED", "TIMED_OUT"):
                    err = status.get("error", state)
                    log.error("RunPodProvider: LTX job %s falhou: %s", job_id, err)
                    return None
                elif attempt % 6 == 0:
                    log.debug(
                        "RunPodProvider: aguardando LTX scene %d... (%ds, status=%s)",
                        scene_id, (attempt + 1) * _SERVERLESS_POLL_INTERVAL, state
                    )
            else:
                log.error(
                    "RunPodProvider: LTX job %s timeout após %ds",
                    job_id, _SERVERLESS_MAX_POLLS * _SERVERLESS_POLL_INTERVAL
                )
                return None

            # --- Passo 3: extrair URL do vídeo ---
            output = status.get("output", {})
            video_url = None

            # Formatos de resposta comuns dos workers LTX no RunPod:
            if isinstance(output, dict):
                video_url = (
                    output.get("video_url")
                    or output.get("video")
                    or output.get("url")
                )
                if not video_url and "videos" in output:
                    videos = output["videos"]
                    if videos:
                        video_url = videos[0] if isinstance(videos[0], str) else videos[0].get("url")
            elif isinstance(output, str):
                # Alguns workers retornam a URL diretamente como string
                video_url = output

            if not video_url:
                log.error("RunPodProvider: output sem URL de vídeo: %s", output)
                return None

            # --- Passo 4: download ---
            if output_dir is None:
                output_dir = Path("batch/videos")
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f"{video_id}_scene{scene_id:03d}_runpod_ltx.mp4"

            dl_req = urllib.request.Request(video_url)
            with urllib.request.urlopen(dl_req, timeout=120) as vr:
                out_path.write_bytes(vr.read())

            log.info("RunPodProvider: LTX scene %d → %s", scene_id, out_path.name)
            return out_path

        except Exception as exc:
            log.error("RunPodProvider: erro LTX serverless scene %d: %s", scene_id, exc)
            return None

    def generate_ltx_serverless(
        self,
        prompt: str,
        duration_seconds: int = 5,
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Wrapper síncrono para generate_ltx_serverless_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.generate_ltx_serverless_async(
                            prompt=prompt,
                            duration_seconds=duration_seconds,
                            scene_id=scene_id,
                            video_id=video_id,
                            output_dir=output_dir,
                        )
                    )
                    return future.result(timeout=700)
            else:
                return loop.run_until_complete(
                    self.generate_ltx_serverless_async(
                        prompt=prompt,
                        duration_seconds=duration_seconds,
                        scene_id=scene_id,
                        video_id=video_id,
                        output_dir=output_dir,
                    )
                )
        except Exception as exc:
            log.error("RunPodProvider: generate_ltx_serverless sync wrapper falhou: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Modo 2 — Wan2.2 via Pod Persistente (WanGP)                          #
    # ------------------------------------------------------------------ #

    async def generate_wan22_pod_async(
        self,
        prompt: str,
        duration_seconds: int = 5,
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
        negative_prompt: str = "blurry, low quality, watermark, text overlay, logo",
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        guidance_scale: float = 5.0,
        num_inference_steps: int = 50,
    ) -> Optional[Path]:
        """
        Gera vídeo via Wan2.2/WanGP no pod persistente RunPod.

        O pod está sempre ativo → zero cold start.
        Endpoint: POST {RUNPOD_WAN22_POD_URL}/generate

        O servidor FastAPI no pod (docker/wan22-pod/server.py) espera:
          {
            "prompt": str,
            "negative_prompt": str,
            "num_frames": int,
            "fps": int,
            "width": int,
            "height": int,
            "guidance_scale": float,
            "num_inference_steps": int
          }
        e retorna:
          { "video_url": str }   ← URL temporária ou base64
        """
        if not self.is_wan22_available():
            log.warning("RunPodProvider: pod Wan2.2 não disponível — RUNPOD_WAN22_POD_URL ausente")
            return None

        import urllib.request
        import urllib.error

        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "num_frames": duration_seconds * fps,
            "fps": fps,
            "width": width,
            "height": height,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
        }

        generate_url = f"{self.wan22_pod_url}/generate"
        log.info(
            "RunPodProvider: gerando Wan2.2 scene %d via pod %s",
            scene_id, self.wan22_pod_url
        )

        try:
            req_data = json.dumps(payload).encode()
            req = urllib.request.Request(
                generate_url, data=req_data,
                headers=self._pod_headers(), method="POST"
            )

            # Pod persistente responde diretamente (sem polling)
            with urllib.request.urlopen(req, timeout=_POD_REQUEST_TIMEOUT) as resp:
                result = json.loads(resp.read())

            # Extrair URL do vídeo da resposta
            video_url = (
                result.get("video_url")
                or result.get("url")
                or result.get("video")
            )

            if not video_url:
                log.error("RunPodProvider: resposta Wan2.2 sem URL de vídeo: %s", result)
                return None

            # Download do vídeo
            if output_dir is None:
                output_dir = Path("batch/videos")
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f"{video_id}_scene{scene_id:03d}_runpod_wan22.mp4"

            # Verificar se é URL HTTP ou dados base64
            if video_url.startswith("http"):
                dl_req = urllib.request.Request(video_url)
                with urllib.request.urlopen(dl_req, timeout=120) as vr:
                    out_path.write_bytes(vr.read())
            elif video_url.startswith("data:video") or video_url.startswith("data:application"):
                # Base64 inline: data:video/mp4;base64,AAAA...
                import base64
                b64_data = video_url.split(",", 1)[1] if "," in video_url else video_url
                out_path.write_bytes(base64.b64decode(b64_data))
            else:
                log.error("RunPodProvider: formato de video_url desconhecido: %s...", video_url[:60])
                return None

            log.info("RunPodProvider: Wan2.2 scene %d → %s", scene_id, out_path.name)
            return out_path

        except Exception as exc:
            log.error("RunPodProvider: erro Wan2.2 pod scene %d: %s", scene_id, exc)
            return None

    def generate_wan22_pod(
        self,
        prompt: str,
        duration_seconds: int = 5,
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """Wrapper síncrono para generate_wan22_pod_async."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.generate_wan22_pod_async(
                            prompt=prompt,
                            duration_seconds=duration_seconds,
                            scene_id=scene_id,
                            video_id=video_id,
                            output_dir=output_dir,
                        )
                    )
                    return future.result(timeout=400)
            else:
                return loop.run_until_complete(
                    self.generate_wan22_pod_async(
                        prompt=prompt,
                        duration_seconds=duration_seconds,
                        scene_id=scene_id,
                        video_id=video_id,
                        output_dir=output_dir,
                    )
                )
        except Exception as exc:
            log.error("RunPodProvider: generate_wan22_pod sync wrapper falhou: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Estimativa de custo                                                   #
    # ------------------------------------------------------------------ #

    def cost_estimate_ltx(self, duration_seconds: int) -> float:
        """Estimativa de custo LTX serverless (hardware A10G ~$0.03/seg)."""
        return round(duration_seconds * 0.03, 4)

    def cost_estimate_wan22(self, duration_seconds: int) -> float:
        """Custo Wan2.2 pod — custo fixo do pod / cenas, estimativa ~$0.02/seg."""
        return round(duration_seconds * 0.02, 4)


# ------------------------------------------------------------------ #
# Singleton                                                             #
# ------------------------------------------------------------------ #

_runpod_provider: Optional[RunPodProvider] = None


def get_runpod_provider() -> RunPodProvider:
    """Retorna a instância singleton do RunPodProvider."""
    global _runpod_provider
    if _runpod_provider is None:
        _runpod_provider = RunPodProvider()
    return _runpod_provider
