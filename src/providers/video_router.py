"""
VideoRouter — roteamento inteligente entre provedores de geração de vídeo.

Hierarquia de provedores por qualidade/custo (outubro 2026):
  Tier 1 Ultra     → Veo3.1 via fal.ai ($0.40-0.60/seg) — hero clips premium
  Tier 2 Premium   → Kling 3.0 via fal.ai ($0.084/seg) — dark/finance padrão
  Tier 3 Budget    → LTX-2.5 Fast via fal.ai ($0.04/seg) — volume alto
  Tier 4 Free      → Wan 2.1 via fal.ai ($0.04/seg) — kids/education
  Fallback         → Higgsfield MCP — sem quota, pago por uso

Roteamento por nicho:
  finance_dark  → Tier 2 (Kling) para cenas padrão, Tier 1 (Veo3) para hero 20%
  dark          → Tier 2 (Kling) ou Tier 3 (LTX)
  kids          → Tier 4 (Wan) ou Tier 3 (LTX)
  tech/education → Tier 3 (LTX Fast) como padrão
"""
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

NICHE_ROUTING = {
    "finance_dark": {
        "premium_provider": "veo3",
        "default_provider": "kling",
        "kling_tier": "turbo_720p",
        "hero_scenes_use_premium": True,
        "hero_scene_ratio": 0.20,
    },
    "dark": {
        "premium_provider": "veo3",
        "default_provider": "kling",
        "kling_tier": "turbo_720p",
        "hero_scenes_use_premium": False,
        "hero_scene_ratio": 0.0,
    },
    "kids": {
        "premium_provider": "kling",
        "default_provider": "kling",
        "kling_tier": "turbo_720p",
        "hero_scenes_use_premium": False,
        "hero_scene_ratio": 0.0,
    },
    "tech": {
        "premium_provider": "kling",
        "default_provider": "kling",
        "kling_tier": "turbo_720p",
        "hero_scenes_use_premium": False,
        "hero_scene_ratio": 0.0,
    },
    "education": {
        "premium_provider": "kling",
        "default_provider": "kling",
        "kling_tier": "turbo_720p",
        "hero_scenes_use_premium": False,
        "hero_scene_ratio": 0.0,
    },
}

HERO_EMOTIONS = {"shock", "suspense", "dread", "revelation"}


@dataclass
class VideoGenerationResult:
    path: Optional[Path]
    provider_used: str
    cost_estimate: float
    scene_id: int


class VideoRouter:
    """
    Roteia geração de vídeo entre Veo3, Kling e Higgsfield com base
    no nicho, emoção da cena e disponibilidade de API keys.
    """

    def __init__(self, niche: str = "dark"):
        self.niche = niche
        self.routing = NICHE_ROUTING.get(niche, NICHE_ROUTING["dark"])

        self._veo3 = None
        self._kling = None
        self._fal = None
        self._higgsfield_available = False

        self._init_providers()

    def _init_providers(self) -> None:
        try:
            from .veo3_provider import get_veo3_provider
            self._veo3 = get_veo3_provider()
        except Exception:
            pass

        try:
            from .kling_provider import get_kling_provider
            self._kling = get_kling_provider(tier=self.routing.get("kling_tier", "turbo_720p"))
        except Exception:
            pass

        try:
            from .fal_provider import get_fal_provider
            self._fal = get_fal_provider()
        except Exception:
            self._fal = None

    def _is_hero_scene(self, scene: dict, scene_index: int, total_scenes: int) -> bool:
        emotion = scene.get("emocao", "").lower()
        if emotion in HERO_EMOTIONS:
            return True
        # First and last scenes are always candidates for hero treatment
        if scene_index == 0 or scene_index == total_scenes - 1:
            return True
        return False

    def estimate_total_cost(self, scenes: list, niche: Optional[str] = None) -> dict:
        routing = NICHE_ROUTING.get(niche or self.niche, NICHE_ROUTING["dark"])
        total = len(scenes)
        hero_count = int(total * routing.get("hero_scene_ratio", 0))
        standard_count = total - hero_count

        # Kling turbo_720p as reference
        kling_cost_per_sec = 0.042
        veo3_cost_per_sec = 0.15
        avg_duration = 6

        hero_cost = hero_count * avg_duration * veo3_cost_per_sec if routing.get("hero_scenes_use_premium") else hero_count * avg_duration * kling_cost_per_sec
        standard_cost = standard_count * avg_duration * kling_cost_per_sec

        return {
            "total_scenes": total,
            "hero_scenes": hero_count,
            "standard_scenes": standard_count,
            "estimated_cost_usd": round(hero_cost + standard_cost, 2),
            "cost_vs_veo3_fast": round((total * avg_duration * veo3_cost_per_sec), 2),
            "savings_pct": round(100 * (1 - (hero_cost + standard_cost) / (total * avg_duration * veo3_cost_per_sec)), 1),
        }

    def generate_scene(
        self,
        scene: dict,
        scene_id: int,
        video_id: str,
        output_dir: Path,
        total_scenes: int = 100,
        force_provider: Optional[str] = None,
    ) -> VideoGenerationResult:
        prompt = scene.get("prompt_visual", "")
        duration = scene.get("duracao_segundos", 5)

        # Decide provider
        use_premium = (
            force_provider == "veo3"
            or (
                not force_provider
                and self.routing.get("hero_scenes_use_premium")
                and self._is_hero_scene(scene, scene_id, total_scenes)
            )
        )

        # Try Veo3 (premium path)
        if use_premium and self._veo3 and self._veo3.is_available():
            result = self._veo3.generate_video(
                prompt=prompt,
                scene_id=scene_id,
                video_id=video_id,
                tier="fast",
                duration_seconds=duration,
                output_dir=output_dir,
            )
            if result:
                cost = 0.15 * duration
                log.info("VideoRouter: scene %d via Veo3 Fast ($%.2f)", scene_id, cost)
                return VideoGenerationResult(path=result, provider_used="veo3_fast", cost_estimate=cost, scene_id=scene_id)

        # Try Kling (default path)
        if force_provider != "veo3" and self._kling and self._kling.is_available():
            tier = force_provider if force_provider in ("standard_720p", "standard_1080p", "turbo_720p", "turbo_1080p") else self.routing.get("kling_tier", "turbo_720p")
            result = self._kling.generate_video(
                prompt=prompt,
                duration_seconds=duration,
                tier=tier,
                scene_id=scene_id,
                video_id=video_id,
                output_dir=output_dir,
            )
            if result:
                cost = self._kling.cost_per_second(tier) * duration
                log.info("VideoRouter: scene %d via Kling %s ($%.3f)", scene_id, tier, cost)
                return VideoGenerationResult(path=result, provider_used=f"kling_{tier}", cost_estimate=cost, scene_id=scene_id)

        # Try fal.ai as fallback (LTX Fast — mais barato, ~$0.04/s)
        if self._fal and self._fal.is_available():
            fal_model = self._fal.select_model(self.niche, quality="standard")
            result = self._fal.generate_video(
                prompt=prompt,
                model_key=fal_model,
                duration_seconds=duration,
                scene_id=scene_id,
                video_id=video_id,
                output_dir=output_dir,
            )
            if result:
                cost = self._fal.cost_per_second(fal_model) * duration
                log.info("VideoRouter: scene %d via fal.ai/%s ($%.3f)", scene_id, fal_model, cost)
                return VideoGenerationResult(path=result, provider_used=f"fal_{fal_model}", cost_estimate=cost, scene_id=scene_id)

        log.warning("VideoRouter: todos os provedores falharam para scene %d — sem vídeo gerado", scene_id)
        return VideoGenerationResult(path=None, provider_used="none", cost_estimate=0.0, scene_id=scene_id)


_routers: dict[str, VideoRouter] = {}


def get_video_router(niche: str = "dark") -> VideoRouter:
    global _routers
    if niche not in _routers:
        _routers[niche] = VideoRouter(niche=niche)
    return _routers[niche]
