"""
KlingProvider — integração com Kling AI API (Kuaishou).

Preços (outubro 2025):
  Kling 3.0 720p sem áudio:  $0.084/seg
  Kling 3.0 1080p sem áudio: $0.112/seg
  Kling 2.5 Turbo 720p:      $0.042/seg  ← melhor custo-benefício
  Kling 2.5 Turbo 1080p:     $0.070/seg

Documentação: https://developer.klingai.com/
"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

KLING_API_BASE = "https://api.klingai.com/v1"

KLING_MODELS = {
    "turbo_720p": {
        "model_name": "kling-v2-5-turbo",
        "resolution": "720p",
        "cost_per_sec": 0.042,
    },
    "turbo_1080p": {
        "model_name": "kling-v2-5-turbo",
        "resolution": "1080p",
        "cost_per_sec": 0.070,
    },
    "standard_720p": {
        "model_name": "kling-v3-0",
        "resolution": "720p",
        "cost_per_sec": 0.084,
    },
    "standard_1080p": {
        "model_name": "kling-v3-0",
        "resolution": "1080p",
        "cost_per_sec": 0.112,
    },
}


class KlingProvider:
    """
    Geração de vídeo via Kling AI API.
    Tier recomendado por nicho:
      - dark/finance padrão: turbo_720p ($0.042/seg)
      - dark/finance premium: standard_1080p ($0.112/seg)
      - kids: turbo_720p ($0.042/seg)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_tier: str = "turbo_720p",
        poll_interval: int = 5,
        max_wait: int = 300,
    ):
        self.api_key = api_key or os.getenv("KLING_API_KEY", "")
        self.default_tier = default_tier
        self.poll_interval = poll_interval
        self.max_wait = max_wait

    def is_available(self) -> bool:
        return bool(self.api_key)

    def cost_per_second(self, tier: Optional[str] = None) -> float:
        t = tier or self.default_tier
        return KLING_MODELS.get(t, KLING_MODELS["turbo_720p"])["cost_per_sec"]

    def estimate_cost(self, duration_seconds: int, tier: Optional[str] = None) -> float:
        return self.cost_per_second(tier) * duration_seconds

    def generate_video(
        self,
        prompt: str,
        duration_seconds: int = 5,
        tier: Optional[str] = None,
        negative_prompt: str = "",
        scene_id: int = 0,
        video_id: str = "",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Gera um clip via Kling API.
        Retorna o Path local do arquivo .mp4 ou None se falhar.
        """
        if not self.is_available():
            log.warning("KlingProvider: KLING_API_KEY não configurada")
            return None

        model_cfg = KLING_MODELS.get(tier or self.default_tier, KLING_MODELS["turbo_720p"])
        payload = {
            "model_name": model_cfg["model_name"],
            "prompt": prompt,
            "negative_prompt": negative_prompt or "blurry, watermark, text overlay, low quality",
            "cfg_scale": 0.5,
            "mode": "std",
            "duration": str(min(duration_seconds, 10)),
        }

        try:
            import urllib.request
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{KLING_API_BASE}/videos/text2video",
                data=data,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())

            task_id = result.get("data", {}).get("task_id")
            if not task_id:
                log.error("KlingProvider: sem task_id na resposta: %s", result)
                return None

            log.info("Kling task %s iniciada (scene %d, %ss, %s)", task_id, scene_id, duration_seconds, tier or self.default_tier)
            return self._poll_and_download(task_id, scene_id, video_id, output_dir)

        except Exception as e:
            log.error("KlingProvider erro ao criar task: %s", e)
            return None

    def _poll_and_download(
        self,
        task_id: str,
        scene_id: int,
        video_id: str,
        output_dir: Optional[Path],
    ) -> Optional[Path]:
        import urllib.request

        deadline = time.time() + self.max_wait
        while time.time() < deadline:
            time.sleep(self.poll_interval)
            try:
                req = urllib.request.Request(
                    f"{KLING_API_BASE}/videos/text2video/{task_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read()).get("data", {})

                status = data.get("task_status", "")
                if status == "succeed":
                    video_url = (
                        data.get("task_result", {})
                        .get("videos", [{}])[0]
                        .get("url", "")
                    )
                    if video_url:
                        return self._download(video_url, task_id, scene_id, video_id, output_dir)
                    log.error("KlingProvider: task succeed mas sem URL de vídeo")
                    return None
                elif status in ("failed", "expired"):
                    log.error("KlingProvider: task %s status=%s", task_id, status)
                    return None
                else:
                    log.debug("Kling task %s: %s…", task_id, status)
            except Exception as e:
                log.warning("KlingProvider poll error: %s", e)

        log.error("KlingProvider: timeout aguardando task %s", task_id)
        return None

    def _download(
        self,
        url: str,
        task_id: str,
        scene_id: int,
        video_id: str,
        output_dir: Optional[Path],
    ) -> Optional[Path]:
        import urllib.request

        if output_dir is None:
            output_dir = Path("batch/visuals")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{video_id}_scene_{scene_id:03d}_kling.mp4"
        dest = output_dir / filename
        try:
            urllib.request.urlretrieve(url, str(dest))
            log.info("Kling scene %d salvo em %s", scene_id, dest)
            return dest
        except Exception as e:
            log.error("KlingProvider download error: %s", e)
            return None


_kling_instance: Optional[KlingProvider] = None


def get_kling_provider(tier: str = "turbo_720p") -> KlingProvider:
    global _kling_instance
    if _kling_instance is None:
        _kling_instance = KlingProvider(default_tier=tier)
    return _kling_instance
