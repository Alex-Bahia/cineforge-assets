"""
CharacterConsistencyManager — Orchestrates the 4-step Método Grid pipeline.

Each channel profile can have a character_reference_url pointing to an image
of the channel's recurring character. This manager uses that reference to:
  1. Generate a 5-panel contact sheet (via Gemini/Google Flow)
  2. For each scene, generate a 2x2 storyboard grid
  3. Extract the best camera angle as a standalone 4K frame
  4. Animate via Veo 3 (or use the static frame as fallback)
"""
import logging
from pathlib import Path
from typing import Optional

from .grid_prompts import (
    REFERENCE_SHEET_PROMPT,
    SCENE_GRID_PROMPT,
    FRAME_EXTRACTION_PROMPT,
    VEO_ANIMATION_PROMPT,
    CAMERA_MOVEMENTS,
    PANEL_ANGLES,
)

log = logging.getLogger(__name__)


class CharacterConsistencyManager:
    """
    Manages consistent character appearance across all video scenes
    using the 4-prompt Método Grid system.
    """

    def __init__(
        self,
        character_name: str,
        character_description: str,
        contact_sheet_path: Optional[Path] = None,
        gemini_client=None,
        veo3_provider=None,
    ):
        self.character_name = character_name
        self.character_description = character_description
        self.contact_sheet_path = contact_sheet_path
        self.gemini_client = gemini_client
        self.veo3_provider = veo3_provider

    def has_contact_sheet(self) -> bool:
        return (
            self.contact_sheet_path is not None
            and Path(self.contact_sheet_path).exists()
        )

    def get_reference_sheet_prompt(self) -> str:
        return REFERENCE_SHEET_PROMPT.format(
            character_description=self.character_description
        )

    def get_scene_grid_prompt(self, scene_description: str) -> str:
        return SCENE_GRID_PROMPT.format(scene_description=scene_description)

    def get_frame_extraction_prompt(self, panel_letter: str = "C") -> str:
        return FRAME_EXTRACTION_PROMPT.format(panel_letter=panel_letter)

    def get_veo_animation_prompt(
        self,
        scene_description: str,
        camera_movement: str = "slow_zoom",
        duration_seconds: int = 5,
    ) -> str:
        movement_desc = CAMERA_MOVEMENTS.get(camera_movement, camera_movement)
        return VEO_ANIMATION_PROMPT.format(
            scene_description=scene_description,
            camera_movement=movement_desc,
            duration_seconds=duration_seconds,
        )

    def select_best_panel(self, scene: dict) -> str:
        """
        Choose camera angle (A/B/C/D) based on scene emotion.
        C (close-up) for emotional moments, A (wide) for establishing shots.
        """
        emotion = scene.get("emocao", "").lower()
        if emotion in ("suspense", "medo", "curiosidade", "shock", "dread"):
            return "C"  # close-up for tension
        elif emotion in ("excitement", "alegria", "inspiracao"):
            return "A"  # wide for energy
        else:
            return "B"  # medium as default

    def get_visual_prompt_with_character(self, scene: dict) -> str:
        """
        Augment the scene's prompt_visual with character consistency instructions.
        Used when full Veo3 pipeline is not available.
        """
        base_prompt = scene.get("prompt_visual", "")
        if not self.character_description:
            return base_prompt
        return (
            f"{base_prompt}. "
            f"Character: {self.character_description}. "
            f"Same person throughout, consistent appearance."
        )

    def generate_scene_visual(
        self,
        scene: dict,
        scene_id: int,
        video_id: str,
        output_dir: Path,
        use_veo3: bool = True,
        veo3_tier: str = "fast",
    ) -> Optional[Path]:
        """
        Full Método Grid pipeline for one scene.
        Falls back gracefully if Veo3 is unavailable.
        """
        scene_desc = scene.get("prompt_visual", scene.get("emocao", "dramatic scene"))
        duration = scene.get("duracao_segundos", 5)

        if use_veo3 and self.veo3_provider and self.veo3_provider.is_available():
            animation_prompt = self.get_veo_animation_prompt(
                scene_description=scene_desc,
                camera_movement="slow_zoom",
                duration_seconds=duration,
            )
            result = self.veo3_provider.generate_video(
                prompt=animation_prompt,
                scene_id=scene_id,
                video_id=video_id,
                tier=veo3_tier,
                duration_seconds=duration,
                reference_image_path=self.contact_sheet_path,
                output_dir=output_dir,
            )
            if result:
                log.info("Character scene %d: Veo3 Método Grid ✓", scene_id)
                return result

        log.info("Character scene %d: Veo3 unavailable, augmenting prompt", scene_id)
        return None

    @classmethod
    def from_profile(cls, profile, gemini_client=None, veo3_provider=None):
        """Create manager from a ChannelProfile that has character fields."""
        character_name = getattr(profile, "character_name", None) or ""
        character_desc = getattr(profile, "character_description", None) or ""
        contact_sheet = getattr(profile, "character_contact_sheet_path", None)
        if contact_sheet:
            contact_sheet = Path(contact_sheet)
        return cls(
            character_name=character_name,
            character_description=character_desc,
            contact_sheet_path=contact_sheet,
            gemini_client=gemini_client,
            veo3_provider=veo3_provider,
        )
