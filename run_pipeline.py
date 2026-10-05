#!/usr/bin/env python3
"""
CineForge — Dark YouTube Channel Automation Pipeline
=====================================================
Run a single video end-to-end:
    python run_pipeline.py "O serial killer mais misterioso do Brasil"

Run the full batch from topics.csv:
    python run_pipeline.py --batch

Schedule daily runs at 06:00:
    python run_pipeline.py --schedule
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Bootstrap ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from config.settings import BATCH_CSV, LOGS, MAX_PARALLEL, SCHEDULE_HOUR, OUTPUT
from src.utils.logger import setup_logging
from src.utils.video_id import make_video_id
from src.utils.sheets import read_csv_topics, mark_csv_status

setup_logging(LOGS)
log = logging.getLogger("cineforge.main")

# ── Pipeline steps (lazy import to avoid circular deps) ───────────────────────
def _import_steps():
    # Files are named 01_... so we use importlib
    import importlib.util, types

    def _load(name: str, path: str):
        spec = importlib.util.spec_from_file_location(name, ROOT / path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    s1 = _load("scriptwriter", "src/pipeline/01_scriptwriter.py")
    s2 = _load("narrator",     "src/pipeline/02_narrator.py")
    s3 = _load("visuals",      "src/pipeline/03_visuals.py")
    s4 = _load("editor",       "src/pipeline/04_editor.py")
    s5 = _load("uploader",     "src/pipeline/05_uploader.py")
    s6 = _load("thumbnail",    "src/pipeline/06_thumbnail.py")

    return (s1.generate_script, s2.synthesize_full_script, s3.fetch_all_visuals,
            s4.assemble_video, s5.upload_video, s6.generate_thumbnail)


def run_single(topic: str, tone: str = "suspense e mistério",
               minutes: int = 8, upload: bool = False,
               publish_at: str | None = None) -> dict:
    """Full pipeline for one video. Returns result dict."""
    (generate_script, synthesize_full_script, fetch_all_visuals,
     assemble_video, upload_video, generate_thumbnail) = _import_steps()

    video_id = make_video_id(topic)
    script_path = OUTPUT / "scripts" / f"{video_id}.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "scripts").mkdir(parents=True, exist_ok=True)

    log.info("═══════════════════════════════════════")
    log.info("VIDEO ID : %s", video_id)
    log.info("TOPIC    : %s", topic)
    log.info("═══════════════════════════════════════")

    result = {"video_id": video_id, "topic": topic, "status": "error", "yt_id": ""}

    try:
        # ── Step 1: Script ────────────────────────────────────────────────────
        log.info("[1/6] Generating script...")
        script = generate_script(topic, tone, minutes, script_path)
        log.info("      ✓ %d scenes, ~%ds", len(script["cenas"]),
                 script.get("duracao_estimada_segundos", 0))

        # ── Step 2: Narration ─────────────────────────────────────────────────
        log.info("[2/6] Synthesizing narration (edge-tts)...")
        narr_results = synthesize_full_script(script, video_id)
        log.info("      ✓ %d audio files generated", len(narr_results))

        # ── Step 3: Visuals ───────────────────────────────────────────────────
        log.info("[3/6] Fetching visuals (Pexels/Pixabay/Pollinations)...")
        visual_paths = fetch_all_visuals(script, video_id)
        found = sum(1 for v in visual_paths if v)
        log.info("      ✓ %d/%d visuals fetched", found, len(visual_paths))

        # ── Step 4: Edit ──────────────────────────────────────────────────────
        log.info("[4/6] Assembling video (MoviePy)...")
        video_path = assemble_video(script, narr_results, visual_paths, video_id)
        log.info("      ✓ Video: %s", video_path)

        # ── Step 5: Thumbnail ─────────────────────────────────────────────────
        log.info("[5/6] Generating thumbnail...")
        thumb_path = generate_thumbnail(script, video_id)
        log.info("      ✓ Thumbnail: %s", thumb_path)

        # ── Step 6: Upload ────────────────────────────────────────────────────
        yt_id = ""
        if upload:
            log.info("[6/6] Uploading to YouTube...")
            yt_id = upload_video(
                video_path=video_path,
                title=script["titulo"],
                description=script["descricao"],
                tags=script.get("tags", []),
                thumbnail_path=thumb_path,
                publish_at=publish_at,
            )
            log.info("      ✓ YouTube: https://youtu.be/%s", yt_id)
        else:
            log.info("[6/6] Upload skipped (use --upload to enable)")

        result = {
            "video_id": video_id,
            "topic": topic,
            "status": "done",
            "yt_id": yt_id,
            "video_path": str(video_path),
            "thumb_path": str(thumb_path),
            "script_path": str(script_path),
            "title": script["titulo"],
        }

    except Exception as e:
        log.exception("Pipeline failed for topic '%s': %s", topic, e)
        result["error"] = str(e)

    return result


def run_batch(csv_path: Path = BATCH_CSV, upload: bool = False,
              auto_schedule: bool = True) -> None:
    """Process all pending topics from CSV sequentially."""
    topics = read_csv_topics(csv_path)
    if not topics:
        log.info("No pending topics in %s", csv_path)
        return

    log.info("Starting batch: %d topics to process", len(topics))

    # Auto-schedule: one per day starting tomorrow 09:00
    base_dt = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    if base_dt < datetime.now(timezone.utc):
        base_dt += timedelta(days=1)

    for i, row in enumerate(topics):
        topic   = row.get("topic", "").strip()
        tone    = row.get("tone", "suspense e mistério").strip()
        minutes = int(row.get("minutes", "8"))

        if not topic:
            continue

        mark_csv_status(csv_path, topic, "processing")

        publish_at = None
        if upload and auto_schedule:
            publish_at = (base_dt + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = run_single(topic, tone, minutes, upload=upload, publish_at=publish_at)
        mark_csv_status(csv_path, topic, result["status"], result.get("yt_id", ""))

        if i < len(topics) - 1:
            log.info("Cooling down 30s before next video...")
            time.sleep(30)

    log.info("Batch complete.")


def run_scheduler() -> None:
    """Run daily at SCHEDULE_HOUR. Blocks indefinitely."""
    import schedule

    def _daily_job():
        log.info("⏰ Scheduled batch starting at %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
        run_batch(upload=True, auto_schedule=True)

    schedule.every().day.at(f"{SCHEDULE_HOUR:02d}:00").do(_daily_job)
    log.info("Scheduler armed: daily at %02d:00. Press Ctrl+C to stop.", SCHEDULE_HOUR)

    while True:
        schedule.run_pending()
        time.sleep(60)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="CineForge — Dark YouTube Automation Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Single video (no upload):
    python run_pipeline.py "O crime que chocou o Brasil"

  Single video + upload (private):
    python run_pipeline.py "O crime que chocou o Brasil" --upload

  Batch from topics.csv (no upload, just render):
    python run_pipeline.py --batch

  Batch + upload + auto-schedule one video per day:
    python run_pipeline.py --batch --upload --auto-schedule

  Run daily scheduler at 06:00:
    python run_pipeline.py --schedule
        """,
    )
    p.add_argument("topic",          nargs="?",             help="Topic for a single video")
    p.add_argument("--tone",         default="suspense e mistério")
    p.add_argument("--minutes",      type=int, default=8)
    p.add_argument("--upload",       action="store_true",   help="Upload to YouTube after render")
    p.add_argument("--publish-at",   help='ISO 8601 schedule "2024-12-31T18:00:00Z"')
    p.add_argument("--batch",        action="store_true",   help="Process all topics from CSV")
    p.add_argument("--csv",          default=str(BATCH_CSV))
    p.add_argument("--auto-schedule",action="store_true",   help="Auto-schedule daily uploads")
    p.add_argument("--schedule",     action="store_true",   help="Run as daily cron daemon")
    args = p.parse_args()

    if args.schedule:
        run_scheduler()
    elif args.batch:
        run_batch(Path(args.csv), upload=args.upload, auto_schedule=args.auto_schedule)
    elif args.topic:
        result = run_single(args.topic, args.tone, args.minutes,
                            upload=args.upload, publish_at=args.publish_at)
        if result["status"] == "done":
            print(f"\n{'═'*60}")
            print(f"✅  Video pronto!")
            print(f"    Título    : {result.get('title', '')}")
            print(f"    Arquivo   : {result.get('video_path', '')}")
            print(f"    Thumbnail : {result.get('thumb_path', '')}")
            if result.get("yt_id"):
                print(f"    YouTube   : https://youtu.be/{result['yt_id']}")
            print(f"{'═'*60}")
        else:
            print(f"\n❌  Falhou: {result.get('error', 'unknown error')}")
            sys.exit(1)
    else:
        p.print_help()
