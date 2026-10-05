"""Step 4 — Assemble video: audio + visuals + subtitles + music via MoviePy/FFmpeg."""
import json
import logging
import random
import sys
from pathlib import Path

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from pydub import AudioSegment, silence

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import (
    ASSETS, OUTPUT,
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_BITRATE, AUDIO_BITRATE,
    SILENCE_THRESHOLD, BACKGROUND_MUSIC_VOLUME,
    SUBTITLE_FONTSIZE, SUBTITLE_COLOR, SUBTITLE_STROKE_COLOR, SUBTITLE_STROKE_WIDTH,
    SUBTITLE_POSITION,
)

log = logging.getLogger(__name__)


# ── Silence removal ────────────────────────────────────────────────────────────

def remove_silence(mp3_path: Path, threshold_dbfs: int = SILENCE_THRESHOLD,
                   min_silence_ms: int = 600, padding_ms: int = 150) -> Path:
    """Strip long silences from narration audio. Returns new cleaned MP3 path."""
    audio = AudioSegment.from_mp3(str(mp3_path))
    chunks = silence.split_on_silence(
        audio,
        min_silence_len=min_silence_ms,
        silence_thresh=threshold_dbfs,
        keep_silence=padding_ms,
    )
    if not chunks:
        return mp3_path

    out_audio = chunks[0]
    for chunk in chunks[1:]:
        out_audio += chunk

    out_path = mp3_path.parent / f"{mp3_path.stem}_clean.mp3"
    out_audio.export(str(out_path), format="mp3", bitrate=AUDIO_BITRATE)
    log.debug("Silence removed: %s → %s", mp3_path.name, out_path.name)
    return out_path


# ── Subtitle clip builder ──────────────────────────────────────────────────────

def make_subtitle_clip(text: str, duration: float, font: str = "Arial",
                       fontsize: int = SUBTITLE_FONTSIZE) -> TextClip:
    """Build a centered subtitle TextClip with stroke."""
    return (
        TextClip(
            text,
            fontsize=fontsize,
            color=SUBTITLE_COLOR,
            font=font,
            stroke_color=SUBTITLE_STROKE_COLOR,
            stroke_width=SUBTITLE_STROKE_WIDTH,
            method="caption",
            size=(VIDEO_WIDTH - 200, None),
            align="center",
        )
        .set_duration(duration)
        .set_position(SUBTITLE_POSITION, relative=True)
    )


def build_subtitle_clips_from_srt(srt_path: Path, video_start: float = 0.0) -> list[TextClip]:
    """Parse SRT and build list of positioned TextClips."""
    import pysrt

    subs = pysrt.open(str(srt_path), encoding="utf-8")
    clips = []
    for sub in subs:
        start = sub.start.ordinal / 1000.0 + video_start
        end   = sub.end.ordinal   / 1000.0 + video_start
        dur   = max(end - start, 0.05)
        txt   = sub.text.replace("\n", " ")
        clip  = make_subtitle_clip(txt, dur).set_start(start)
        clips.append(clip)
    return clips


# ── Visual clip builder ────────────────────────────────────────────────────────

def _apply_kenburns(clip: ImageClip, duration: float) -> ImageClip:
    """Slow zoom-in Ken Burns effect to add motion to static images."""
    zoom_start, zoom_end = 1.0, 1.12
    def zoom(t):
        scale = zoom_start + (zoom_end - zoom_start) * (t / duration)
        return scale
    return clip.resize(zoom)


def build_visual_clip(asset_path: Path, duration: float,
                      kenburns: bool = True) -> CompositeVideoClip | ImageClip:
    """Build a video/image clip cropped to VIDEO_WIDTH x VIDEO_HEIGHT."""
    if asset_path is None:
        return ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(10, 10, 20), duration=duration)

    ext = asset_path.suffix.lower()

    if ext in {".mp4", ".mov", ".avi", ".webm"}:
        clip = (
            VideoFileClip(str(asset_path), audio=False)
            .without_audio()
        )
        # Loop if shorter than needed
        if clip.duration < duration:
            loops = int(np.ceil(duration / clip.duration))
            from moviepy.editor import concatenate_videoclips
            clip = concatenate_videoclips([clip] * loops)
        clip = clip.subclip(0, duration)
    else:
        clip = ImageClip(str(asset_path), duration=duration)
        if kenburns:
            clip = _apply_kenburns(clip, duration)

    # Resize + crop to target resolution
    clip = (
        clip
        .resize(height=VIDEO_HEIGHT)
        .crop(x_center=clip.w / 2 if hasattr(clip, "w") else VIDEO_WIDTH / 2,
              width=VIDEO_WIDTH)
        .set_duration(duration)
    )
    return clip


# ── Music bed ─────────────────────────────────────────────────────────────────

def get_background_music(total_duration: float) -> AudioFileClip | None:
    """Pick a random music file from assets/music, loop to fill duration."""
    music_dir = ASSETS / "music"
    files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
    if not files:
        log.warning("No music files in assets/music — video will have no background music.")
        return None

    music_file = random.choice(files)
    music = AudioFileClip(str(music_file)).volumex(BACKGROUND_MUSIC_VOLUME)

    if music.duration < total_duration:
        loops = int(np.ceil(total_duration / music.duration))
        from moviepy.editor import concatenate_audioclips
        music = concatenate_audioclips([music] * loops)

    return music.subclip(0, total_duration).audio_fadein(2).audio_fadeout(3)


# ── Full assembly ──────────────────────────────────────────────────────────────

def assemble_video(
    script: dict,
    narration_results: list[dict],
    visual_paths: list[Path | None],
    video_id: str,
    burn_subtitles: bool = True,
    add_music: bool = True,
) -> Path:
    """
    Assemble all scenes into a final MP4.
    Returns path to rendered video.
    """
    video_clips = []
    all_audio   = []
    sub_clips   = []
    timeline    = 0.0

    for i, (narr, visual) in enumerate(zip(narration_results, visual_paths)):
        scene   = narr["scene"]
        mp3     = narr["mp3"]
        srt     = narr["srt"]

        # Clean audio
        clean_mp3 = remove_silence(mp3)
        narration_audio = AudioFileClip(str(clean_mp3))
        duration = narration_audio.duration

        # Visual
        vis_clip = build_visual_clip(visual, duration)

        # Combine visual + narration
        vis_clip = vis_clip.set_audio(narration_audio)
        video_clips.append(vis_clip)

        # Subtitles from SRT
        if burn_subtitles and srt.exists():
            scene_subs = build_subtitle_clips_from_srt(srt, video_start=timeline)
            sub_clips.extend(scene_subs)

        timeline += duration
        log.info("Scene %d assembled (%.1fs, total %.1fs)", scene["id"], duration, timeline)

    # Concatenate all scene clips
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Burn subtitles on top
    if sub_clips:
        final_video = CompositeVideoClip([final_video] + sub_clips)

    # Add background music
    if add_music:
        music = get_background_music(final_video.duration)
        if music:
            mixed = CompositeAudioClip([final_video.audio, music])
            final_video = final_video.set_audio(mixed)

    # Render
    out_dir = OUTPUT / "videos"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{video_id}.mp4"

    final_video.write_videofile(
        str(out_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate=VIDEO_BITRATE,
        audio_bitrate=AUDIO_BITRATE,
        threads=4,
        preset="fast",
        logger="bar",
    )

    log.info("✅ Video rendered: %s (%.1f seconds)", out_path, final_video.duration)
    return out_path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    p = argparse.ArgumentParser(description="Assemble video from pipeline outputs")
    p.add_argument("video_id", help="Video ID used in steps 1-3")
    p.add_argument("--script", required=True, help="Path to script JSON")
    p.add_argument("--no-music", action="store_true")
    p.add_argument("--no-subs",  action="store_true")
    args = p.parse_args()

    import importlib, sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    narrator = importlib.import_module("02_narrator")
    visuals  = importlib.import_module("03_visuals")

    script = json.loads(Path(args.script).read_text())

    # Reconstruct paths from previous steps
    audio_dir = OUTPUT / "audio" / args.video_id
    sub_dir   = OUTPUT / "subtitles" / args.video_id
    img_dir   = OUTPUT / "images" / args.video_id

    narr_results = []
    vis_paths    = []
    for scene in script["cenas"]:
        mp3s = sorted(audio_dir.glob(f"scene_{scene['id']:03d}*.mp3"))
        srts = sorted(sub_dir.glob(f"scene_{scene['id']:03d}*.srt"))
        imgs = sorted(img_dir.glob(f"scene_{scene['id']:03d}*"))
        narr_results.append({
            "scene": scene,
            "mp3": mp3s[0] if mp3s else None,
            "srt": srts[0] if srts else Path("/dev/null"),
        })
        vis_paths.append(imgs[0] if imgs else None)

    out = assemble_video(
        script, narr_results, vis_paths, args.video_id,
        burn_subtitles=not args.no_subs,
        add_music=not args.no_music,
    )
    print(f"\n✅ Final video: {out}")
