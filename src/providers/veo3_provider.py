"""
Veo 3 Provider — Google Vertex AI video generation.

Pricing (per second of video generated):
  Lite:     $0.03/sec  — b-roll, backgrounds, simple scenes
  Fast:     $0.15/sec  — main scenes, good quality
  Standard: $0.75/sec  — hero shots, cinematic quality

Usage:
    from src.providers.veo3_provider import Veo3Provider
    provider = Veo3Provider()
    video_path = provider.generate_video(
        prompt="A dark office with a CEO looking at screens full of financial data",
        scene_id=1,
        video_id="my_video",
        tier="fast",
        duration_seconds=5,
        reference_image_path=None,  # optional character contact sheet
    )
"""
import logging
import os
import time
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

VEO3_TIERS = {
    "lite":     {"model": "veo-3.0-fast-generate-001", "cost_per_sec": 0.03},
    "fast":     {"model": "veo-3.0-fast-generate-001", "cost_per_sec": 0.15},
    "standard": {"model": "veo-3.0-generate-001",      "cost_per_sec": 0.75},
}


class Veo3Provider:
    """Google Vertex AI Veo 3 video generation provider."""

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.location = location
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import vertexai
                from vertexai.preview.vision_models import VideoGenerationModel
                vertexai.init(project=self.project_id, location=self.location)
                self._client = VideoGenerationModel
            except ImportError:
                raise ImportError(
                    "google-cloud-aiplatform não instalado. "
                    "Execute: pip install google-cloud-aiplatform"
                )
        return self._client

    def is_available(self) -> bool:
        if not self.project_id:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def generate_video(
        self,
        prompt: str,
        scene_id: int,
        video_id: str,
        tier: str = "fast",
        duration_seconds: int = 5,
        reference_image_path: Optional[Path] = None,
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Generate a video clip using Veo 3.
        Returns local path to generated .mp4, or None on failure.
        """
        if not self.is_available():
            log.warning("Veo3: GOOGLE_CLOUD_PROJECT não configurado. Usando fallback.")
            return None

        tier_config = VEO3_TIERS.get(tier, VEO3_TIERS["fast"])
        model_id = tier_config["model"]
        estimated_cost = duration_seconds * tier_config["cost_per_sec"]

        if output_dir is None:
            output_dir = Path("output") / "images" / video_id
        output_dir.mkdir(parents=True, exist_ok=True)

        dest = output_dir / f"scene_{scene_id:03d}_veo3_{tier}.mp4"
        if dest.exists():
            log.info("Veo3 cache hit: %s", dest.name)
            return dest

        log.info(
            "Veo3 [%s] scene %d: generating %ds video (est. $%.2f)...",
            tier, scene_id, duration_seconds, estimated_cost,
        )

        try:
            VideoGenerationModel = self._get_client()
            model = VideoGenerationModel.from_pretrained(model_id)

            generate_kwargs = {
                "prompt": prompt,
                "duration_seconds": duration_seconds,
                "aspect_ratio": "16:9",
                "resolution": "1080p",
            }

            if reference_image_path and Path(reference_image_path).exists():
                from vertexai.preview.vision_models import Image as VertexImage
                generate_kwargs["image"] = VertexImage.load_from_file(str(reference_image_path))

            response = model.generate_video(**generate_kwargs)

            # Poll for completion (up to 5 minutes)
            max_wait = 300
            elapsed = 0
            while elapsed < max_wait:
                if hasattr(response, 'done') and response.done():
                    break
                time.sleep(10)
                elapsed += 10
                log.debug("Veo3: waiting... %ds elapsed", elapsed)

            if hasattr(response, 'videos') and response.videos:
                video = response.videos[0]
                if hasattr(video, 'save'):
                    video.save(str(dest))
                elif hasattr(video, '_video_bytes'):
                    dest.write_bytes(video._video_bytes)
                log.info("Veo3 ✓ scene %d: saved to %s", scene_id, dest.name)
                return dest
            else:
                log.error("Veo3: empty response for scene %d", scene_id)
                return None

        except Exception as e:
            log.error("Veo3 generation failed for scene %d: %s", scene_id, e)
            return None

    def estimate_cost(self, scenes: list, tier: str = "fast") -> float:
        """Estimate total cost for a list of scenes."""
        cost_per_sec = VEO3_TIERS.get(tier, VEO3_TIERS["fast"])["cost_per_sec"]
        total_seconds = sum(s.get("duracao_segundos", 5) for s in scenes)
        return total_seconds * cost_per_sec


_provider: Optional[Veo3Provider] = None


def get_veo3_provider() -> Veo3Provider:
    global _provider
    if _provider is None:
        _provider = Veo3Provider()
    return _provider
