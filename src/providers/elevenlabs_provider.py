"""
ElevenLabs TTS Provider — Premium voice synthesis.

ElevenLabs achieves 58-68% viewer retention vs 35-45% for basic TTS.
Use for high-RPM channels (US finance dark, US dark) where quality matters most.

Pricing (2025):
  Starter: $5/month  — 30,000 chars/month
  Creator: $22/month — 100,000 chars/month
  Pro:     $99/month — 500,000 chars/month

Usage:
    from src.providers.elevenlabs_provider import ElevenLabsProvider
    provider = ElevenLabsProvider()
    if provider.is_available():
        mp3_path = provider.synthesize(text, scene_id, video_id, voice_id)
"""
import logging
import os
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ElevenLabs built-in voice IDs
ELEVENLABS_VOICES = {
    "en-US-male-dark":  "onwK4e9ZLuTAKqWW03F9",  # Daniel — deep, narrative
    "en-US-male-news":  "N2lVS1w4EtoT3dr4eOWO",  # Callum — authoritative
    "en-US-female":     "21m00Tcm4TlvDq8ikWAM",  # Rachel — warm
    "en-GB-male":       "VR6AewLTigWG4xSOukaG",  # Arnold — British
    "pt-BR-male":       "pNInz6obpgDQGcFmaJgB",  # Adam (deep narration)
    "pt-BR-male-dark":  "onwK4e9ZLuTAKqWW03F9",  # Daniel — deep
    "es-ES-male":       "g5CIjZEefAph4nQFvHAz",  # Fin
    "fr-FR-male":       "XrExE9yKIg1WjnnlVkGX",  # Liam
    "de-DE-male":       "IKne3meq5aSn9XLyUdCD",  # Charlie
}

ELEVENLABS_SETTINGS = {
    "dark":        {"stability": 0.75, "similarity_boost": 0.85, "style": 0.3},
    "finance":     {"stability": 0.8,  "similarity_boost": 0.85, "style": 0.2},
    "finance_dark":{"stability": 0.78, "similarity_boost": 0.87, "style": 0.25},
    "news":        {"stability": 0.85, "similarity_boost": 0.9,  "style": 0.1},
    "default":     {"stability": 0.7,  "similarity_boost": 0.8,  "style": 0.3},
}


class ElevenLabsProvider:
    """ElevenLabs text-to-speech provider for premium voice quality."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def synthesize(
        self,
        text: str,
        scene_id: int,
        video_id: str,
        voice_id: Optional[str] = None,
        niche: str = "dark",
        output_dir: Optional[Path] = None,
    ) -> Optional[Path]:
        """
        Synthesize text to MP3 using ElevenLabs API.
        Returns local path to MP3, or None on failure.
        """
        if not self.is_available():
            log.warning("ElevenLabs: API key not set. Configure ELEVENLABS_API_KEY.")
            return None

        import requests

        if voice_id is None:
            voice_id = ELEVENLABS_VOICES.get("en-US-male-dark")

        if output_dir is None:
            output_dir = Path("output") / "audio" / video_id
        output_dir.mkdir(parents=True, exist_ok=True)

        dest = output_dir / f"scene_{scene_id:03d}_el.mp3"
        if dest.exists():
            log.info("ElevenLabs cache hit: %s", dest.name)
            return dest

        voice_settings = ELEVENLABS_SETTINGS.get(niche, ELEVENLABS_SETTINGS["default"])

        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": voice_settings,
        }
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=60)
            r.raise_for_status()
            dest.write_bytes(r.content)
            log.info("ElevenLabs ✓ scene %d: %s", scene_id, dest.name)
            return dest
        except Exception as e:
            log.error("ElevenLabs failed scene %d: %s", scene_id, e)
            return None

    def get_voice_id_for_profile(self, profile) -> str:
        """Get ElevenLabs voice ID for a channel profile."""
        custom = getattr(profile, "elevenlabs_voice_id", None)
        if custom:
            return custom

        lang = getattr(profile, "language", "en-US")
        niche = getattr(profile, "niche", "dark")

        key = f"{lang}-male-{niche}"
        if key in ELEVENLABS_VOICES:
            return ELEVENLABS_VOICES[key]

        for voice_key, voice_id in ELEVENLABS_VOICES.items():
            if voice_key.startswith(lang[:5]):
                return voice_id

        return ELEVENLABS_VOICES["en-US-male-dark"]

    def estimate_cost(self, scenes: list) -> dict:
        total_chars = sum(len(s.get("texto_narracao", "")) for s in scenes)
        return {
            "total_characters": total_chars,
            "starter_remaining_pct": max(0, (30000 - total_chars) / 30000 * 100),
            "note": "Starter: 30k chars/month ($5). Creator: 100k/month ($22).",
        }


_provider: Optional[ElevenLabsProvider] = None


def get_elevenlabs_provider() -> ElevenLabsProvider:
    global _provider
    if _provider is None:
        _provider = ElevenLabsProvider()
    return _provider
