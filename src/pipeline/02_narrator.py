"""Step 2 — Convert script narration to MP3 + SRT via edge-tts (free, unlimited)."""
import asyncio
import json
import logging
import re
import sys
from pathlib import Path

import edge_tts
try:
    from src.providers.elevenlabs_provider import get_elevenlabs_provider
    _ELEVENLABS_AVAILABLE = True
except ImportError:
    _ELEVENLABS_AVAILABLE = False
import pysrt

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import (
    OUTPUT, TTS_VOICE, TTS_RATE, TTS_PITCH
)

log = logging.getLogger(__name__)


async def _synthesize(text: str, voice: str, rate: str, pitch: str,
                      mp3_path: Path, srt_path: Path) -> None:
    """Run edge-tts synthesis and write MP3 + SRT word-level subtitles."""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    sub_maker = edge_tts.SubMaker()

    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.create_sub(
                    (chunk["offset"], chunk["duration"]),
                    chunk["text"],
                )

    srt_path.write_text(sub_maker.generate_subs(), encoding="utf-8")
    log.info("Audio: %s  Subtitles: %s", mp3_path.name, srt_path.name)


def synthesize_scene(scene_text: str, scene_id: int, video_id: str,
                     voice: str = TTS_VOICE,
                     rate: str = TTS_RATE,
                     pitch: str = TTS_PITCH) -> tuple[Path, Path]:
    """Synthesize one scene. Returns (mp3_path, srt_path)."""
    audio_dir = OUTPUT / "audio" / video_id
    sub_dir   = OUTPUT / "subtitles" / video_id
    audio_dir.mkdir(parents=True, exist_ok=True)
    sub_dir.mkdir(parents=True, exist_ok=True)

    mp3 = audio_dir / f"scene_{scene_id:03d}.mp3"
    srt = sub_dir   / f"scene_{scene_id:03d}.srt"

    asyncio.run(_synthesize(scene_text, voice, rate, pitch, mp3, srt))
    return mp3, srt


def synthesize_scene_premium(
    scene_text: str,
    scene_id: int,
    video_id: str,
    voice_id: str = None,
    niche: str = "dark",
    tts_tier: str = "free",
) -> tuple:
    """Synthesize with tier selection. 'premium' uses ElevenLabs; 'free' uses edge-tts."""
    if tts_tier == "premium" and _ELEVENLABS_AVAILABLE:
        provider = get_elevenlabs_provider()
        if provider.is_available():
            audio_dir = OUTPUT / "audio" / video_id
            mp3 = provider.synthesize(
                text=scene_text,
                scene_id=scene_id,
                video_id=video_id,
                voice_id=voice_id,
                niche=niche,
                output_dir=audio_dir,
            )
            if mp3:
                log.info("Scene %d: ElevenLabs premium TTS ✓", scene_id)
                srt = _generate_approximate_srt(mp3, scene_text, scene_id, video_id)
                return mp3, srt

    return synthesize_scene(scene_text, scene_id, video_id)


def _generate_approximate_srt(mp3_path, text: str, scene_id: int, video_id: str):
    """Generate approximate SRT timing from MP3 duration and word count."""
    import math
    sub_dir = OUTPUT / "subtitles" / video_id
    sub_dir.mkdir(parents=True, exist_ok=True)
    srt = sub_dir / f"scene_{scene_id:03d}.srt"

    try:
        duration = get_audio_duration(mp3_path)
        words = text.split()
        words_per_sub = 4
        sub_duration = duration / max(1, math.ceil(len(words) / words_per_sub))

        lines = []
        for i, chunk_start in enumerate(range(0, len(words), words_per_sub)):
            chunk = " ".join(words[chunk_start:chunk_start + words_per_sub])
            t_start = chunk_start / max(1, len(words)) * duration
            t_end = min(t_start + sub_duration, duration)

            def fmt_time(t):
                h, rem = divmod(t, 3600)
                m, s = divmod(rem, 60)
                ms = int((s % 1) * 1000)
                return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"

            lines.extend([str(i + 1), f"{fmt_time(t_start)} --> {fmt_time(t_end)}", chunk, ""])

        srt.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        log.warning("Could not generate approximate SRT: %s", e)
        srt.write_text("", encoding="utf-8")

    return srt


def synthesize_full_script_with_tier(
    script: dict,
    video_id: str,
    tts_tier: str = "free",
    voice: str = TTS_VOICE,
    rate: str = TTS_RATE,
    pitch: str = TTS_PITCH,
    elevenlabs_voice_id: str = None,
    niche: str = "dark",
) -> list:
    """Synthesize all scenes with tier selection (free=edge-tts, premium=ElevenLabs)."""
    results = []
    for scene in script["cenas"]:
        if tts_tier == "premium":
            mp3, srt = synthesize_scene_premium(
                scene["texto_narracao"],
                scene["id"],
                video_id,
                voice_id=elevenlabs_voice_id,
                niche=niche,
                tts_tier=tts_tier,
            )
        else:
            mp3, srt = synthesize_scene(
                scene["texto_narracao"], scene["id"], video_id, voice, rate, pitch
            )
        results.append({"scene": scene, "mp3": mp3, "srt": srt})
        log.info("Scene %d/%d narrated [%s]", scene["id"], len(script["cenas"]), tts_tier)
    return results


def synthesize_full_script(script: dict, video_id: str,
                            voice: str = TTS_VOICE,
                            rate: str = TTS_RATE,
                            pitch: str = TTS_PITCH) -> list[dict]:
    """Synthesize all scenes. Returns list of {scene, mp3, srt} dicts."""
    results = []
    for scene in script["cenas"]:
        mp3, srt = synthesize_scene(
            scene["texto_narracao"], scene["id"], video_id, voice, rate, pitch
        )
        results.append({"scene": scene, "mp3": mp3, "srt": srt})
        log.info("Scene %d/%d narrated", scene["id"], len(script["cenas"]))
    return results


def get_audio_duration(mp3_path: Path) -> float:
    """Return MP3 duration in seconds using pydub."""
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(str(mp3_path))
    return len(audio) / 1000.0


def merge_srt_files(srt_paths: list[Path], durations: list[float],
                    out_path: Path) -> Path:
    """Merge per-scene SRT files into one full-video SRT with correct offsets."""
    merged = pysrt.SubRipFile()
    offset = 0.0

    for srt_path, duration in zip(srt_paths, durations):
        try:
            subs = pysrt.open(str(srt_path), encoding="utf-8")
            for sub in subs:
                sub.shift(milliseconds=int(offset * 1000))
                sub.index = len(merged) + 1
                merged.append(sub)
            offset += duration
        except Exception as e:
            log.warning("Could not merge %s: %s", srt_path, e)

    merged.save(str(out_path), encoding="utf-8")
    log.info("Merged SRT saved to %s (%d entries)", out_path, len(merged))
    return out_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Narrate a script JSON with edge-tts")
    p.add_argument("script_json", help="Path to script JSON from step 1")
    p.add_argument("--video-id", default="test_video")
    p.add_argument("--voice", default=TTS_VOICE)
    args = p.parse_args()

    script = json.loads(Path(args.script_json).read_text())
    results = synthesize_full_script(script, args.video_id, args.voice)
    print(f"\n✅ Narrated {len(results)} scenes for video '{args.video_id}'")
