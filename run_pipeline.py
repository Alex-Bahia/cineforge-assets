#!/usr/bin/env python3
"""
CineForge — Universal YouTube Channel Automation Pipeline
==========================================================
Create videos for ANY market (Brazil, USA, Europe) and ANY niche
(dark, sports, kids, tech, finance, education, health, entertainment, cooking...).

Run a single video:
    python run_pipeline.py "O serial killer mais misterioso do Brasil"
    python run_pipeline.py "The most mysterious serial killer in US history" --profile us_dark
    python run_pipeline.py "Champions League best goals this week" --profile br_sports
    python run_pipeline.py "How to invest in the S&P 500" --profile us_finance

Run the full batch from topics.csv:
    python run_pipeline.py --batch

List available channel profiles:
    python run_pipeline.py --list-profiles

Schedule daily runs:
    python run_pipeline.py --schedule
"""
import argparse
import asyncio
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
    import importlib.util

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


def run_single(
    topic: str,
    tone: str = "",
    minutes: int = 8,
    upload: bool = False,
    publish_at: str | None = None,
    profile_id: str = "br_dark",
) -> dict:
    """Full pipeline for one video. Returns result dict."""
    from config.channel_profiles import get_profile

    (generate_script, synthesize_full_script, fetch_all_visuals,
     assemble_video, upload_video, generate_thumbnail) = _import_steps()

    # Load channel profile
    profile = get_profile(profile_id)
    effective_tone = tone or ""

    video_id = make_video_id(topic)
    script_path = OUTPUT / "scripts" / f"{video_id}.json"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "scripts").mkdir(parents=True, exist_ok=True)

    log.info("═══════════════════════════════════════")
    log.info("VIDEO ID : %s", video_id)
    log.info("TOPIC    : %s", topic)
    log.info("PROFILE  : %s (%s / %s)", profile.id, profile.market, profile.niche)
    log.info("LANGUAGE : %s  VOICE: %s", profile.language, profile.tts_voice)
    log.info("═══════════════════════════════════════")

    result = {"video_id": video_id, "topic": topic, "status": "error", "yt_id": "",
              "profile": profile_id, "market": profile.market, "niche": profile.niche}

    try:
        # ── Step 1: Script ────────────────────────────────────────────────────
        log.info("[1/6] Generating script...")
        script = generate_script(
            topic=topic,
            tone=effective_tone,
            duration_min=minutes,
            output_path=script_path,
            language=profile.language,
            niche=profile.niche,
            audience=profile.audience,
            content_style=profile.content_style,
            content_rating=profile.content_rating,
        )
        log.info("      ✓ %d scenes, ~%ds", len(script["cenas"]),
                 script.get("duracao_estimada_segundos", 0))

        # ── Step 2: Narration ─────────────────────────────────────────────────
        log.info("[2/6] Synthesizing narration (%s)...", profile.tts_voice)
        narr_results = synthesize_full_script(
            script, video_id,
            voice=profile.tts_voice,
            rate=profile.tts_rate,
            pitch=profile.tts_pitch,
        )
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
        thumb_path = generate_thumbnail(script, video_id, niche=profile.niche)
        log.info("      ✓ Thumbnail: %s", thumb_path)

        # ── Step 6: Upload ────────────────────────────────────────────────────
        yt_id = ""
        if upload:
            log.info("[6/6] Uploading to YouTube...")
            yt_id = upload_video(
                video_path=video_path,
                title=script["titulo"],
                description=script["descricao"],
                tags=script.get("tags", []) + profile.extra_tags,
                thumbnail_path=thumb_path,
                publish_at=publish_at,
                category_id=profile.yt_category_id,
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
            "profile": profile_id,
            "market": profile.market,
            "niche": profile.niche,
            "language": profile.language,
        }

    except Exception as e:
        log.exception("Pipeline failed for topic '%s': %s", topic, e)
        result["error"] = str(e)

    return result


def run_batch(csv_path: Path = BATCH_CSV, upload: bool = False,
              auto_schedule: bool = True,
              default_profile: str = "br_dark") -> None:
    """Process all pending topics from CSV sequentially."""
    topics = read_csv_topics(csv_path)
    if not topics:
        log.info("No pending topics in %s", csv_path)
        return

    log.info("Starting batch: %d topics to process", len(topics))

    base_dt = datetime.now(timezone.utc).replace(hour=9, minute=0, second=0, microsecond=0)
    if base_dt < datetime.now(timezone.utc):
        base_dt += timedelta(days=1)

    for i, row in enumerate(topics):
        topic   = row.get("topic", "").strip()
        tone    = row.get("tone", "").strip()
        minutes = int(row.get("minutes", "8"))
        # CSV can have a 'profile' column; falls back to default_profile
        profile = row.get("profile", default_profile).strip() or default_profile

        if not topic:
            continue

        mark_csv_status(csv_path, topic, "processing")

        publish_at = None
        if upload and auto_schedule:
            publish_at = (base_dt + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ")

        result = run_single(topic, tone, minutes, upload=upload,
                           publish_at=publish_at, profile_id=profile)
        mark_csv_status(csv_path, topic, result["status"], result.get("yt_id", ""))

        if i < len(topics) - 1:
            log.info("Cooling down 30s before next video...")
            time.sleep(30)

    log.info("Batch complete.")


async def run_hunt(
    n_niches: int = 5,
    n_topics: int = 8,
    dry_run: bool = False,
    no_grounding: bool = False,
    region: str = "BR",
    language: str = "pt-BR",
) -> None:
    """Discover new channel opportunities and feed topics into the pipeline queue."""
    from src.research.channel_hunter import ChannelHunter

    hunter = ChannelHunter(
        use_grounding=not no_grounding,
        region=region,
        language=language,
    )
    opportunities = await hunter.hunt(n_niches=n_niches, n_topics_per_niche=n_topics)
    report_path = hunter.save_report(opportunities)

    print(f"\n{'═'*60}")
    print(f"CHANNEL HUNT COMPLETE — Market: {region} | Language: {language}")
    print(f"{'═'*60}")
    print(f"Niches analysed   : {len(opportunities)}")
    print(f"Total topics found: {sum(len(o.video_topics) for o in opportunities)}")
    print(f"Full report       : {report_path}")

    if not dry_run:
        n_added = hunter.save_to_csv(opportunities)
        print(f"Added {n_added} new topics to batch/topics.csv")
    else:
        print("[dry-run] topics.csv NOT modified")

    if opportunities:
        print("\nTOP 3 NICHES:")
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"  #{i} {opp.name}")
            print(f"     Score: {opp.score:.1f}/10 | CPM: ${opp.estimated_cpm_usd:.2f} "
                  f"| Competition: {opp.competition_level}")


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


def list_profiles_cmd():
    from config.channel_profiles import PROFILES, get_markets, get_niches
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║              AVAILABLE CHANNEL PROFILES                     ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")

    markets = get_markets()
    for market in markets:
        mprofiles = [p for p in PROFILES.values() if p.market == market]
        flag = {"BR": "🇧🇷", "US": "🇺🇸", "GB": "🇬🇧", "FR": "🇫🇷",
                "DE": "🇩🇪", "ES": "🇪🇸", "IT": "🇮🇹"}.get(market, "🌍")
        print(f"  {flag}  MARKET: {market}")
        for p in mprofiles:
            print(f"      --profile {p.id:<20} [{p.niche:<14}] {p.language}  voice: {p.tts_voice}")
        print()

    print(f"  Available niches  : {', '.join(get_niches())}")
    print(f"  Available markets : {', '.join(markets)}")
    print()
    print("  Usage:")
    print('    python run_pipeline.py "Topic here" --profile us_dark')
    print('    python run_pipeline.py "Tema aqui"  --profile br_sports')
    print('    python run_pipeline.py --batch --profile fr_dark')
    print()


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="CineForge — Universal YouTube Automation (any market, any niche)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Brazil dark channel (default):
    python run_pipeline.py "O crime que chocou o Brasil"

  USA dark channel:
    python run_pipeline.py "The most haunting unsolved murder" --profile us_dark

  UK education:
    python run_pipeline.py "The untold story of the Roman Empire" --profile gb_education

  Brazil sports:
    python run_pipeline.py "Os 10 gols mais bonitos do Brasileirão" --profile br_sports

  France dark:
    python run_pipeline.py "Le crime parfait qui a fasciné la France" --profile fr_dark

  Germany tech:
    python run_pipeline.py "Die 5 besten KI-Tools für 2026" --profile de_tech

  USA finance:
    python run_pipeline.py "How I turned $1000 into $50000 in one year" --profile us_finance

  Batch from CSV:
    python run_pipeline.py --batch --profile br_dark

  List all profiles:
    python run_pipeline.py --list-profiles

  Hunt new opportunities (Brazil):
    python run_pipeline.py --hunt --region BR

  Hunt new opportunities (USA):
    python run_pipeline.py --hunt --region US --language en-US
        """,
    )
    p.add_argument("topic",              nargs="?",            help="Topic for a single video")
    p.add_argument("--tone",             default="")
    p.add_argument("--minutes",          type=int, default=8)
    p.add_argument("--upload",           action="store_true",  help="Upload to YouTube after render")
    p.add_argument("--publish-at",       help='ISO 8601 schedule "2024-12-31T18:00:00Z"')
    p.add_argument("--batch",            action="store_true",  help="Process all topics from CSV")
    p.add_argument("--csv",              default=str(BATCH_CSV))
    p.add_argument("--auto-schedule",    action="store_true",  help="Auto-schedule daily uploads")
    p.add_argument("--schedule",         action="store_true",  help="Run as daily cron daemon")
    # ── Channel profile ───────────────────────────────────────────────────────
    p.add_argument("--profile",          default="br_dark",
                   help="Channel profile ID (default: br_dark). See --list-profiles")
    p.add_argument("--list-profiles",    action="store_true",
                   help="List all available channel profiles and exit")
    # ── Channel discovery ─────────────────────────────────────────────────────
    p.add_argument("--hunt",             action="store_true",
                   help="Discover new channel niches and add topics to queue")
    p.add_argument("--hunt-niches",      type=int, default=5)
    p.add_argument("--hunt-topics",      type=int, default=8)
    p.add_argument("--hunt-dry-run",     action="store_true")
    p.add_argument("--region",           default="BR",
                   help="Market region for hunt: BR, US, GB, FR, DE, ES, IT")
    p.add_argument("--language",         default="",
                   help="Override language for hunt (auto-detected from region if empty)")
    p.add_argument("--monitor",          action="store_true",
                   help="Run continuous trend monitor")
    p.add_argument("--monitor-interval", type=float, default=12.0)
    args = p.parse_args()

    if args.list_profiles:
        list_profiles_cmd()

    elif args.hunt:
        # Auto-detect language from region if not specified
        region_lang = {
            "BR": "pt-BR", "PT": "pt-PT",
            "US": "en-US", "GB": "en-GB", "AU": "en-AU",
            "FR": "fr-FR", "DE": "de-DE", "ES": "es-ES",
            "IT": "it-IT", "NL": "nl-NL", "PL": "pl-PL",
        }
        language = args.language or region_lang.get(args.region.upper(), "en-US")
        asyncio.run(run_hunt(
            n_niches=args.hunt_niches,
            n_topics=args.hunt_topics,
            dry_run=args.hunt_dry_run,
            region=args.region,
            language=language,
        ))

    elif args.monitor:
        from src.research.trend_monitor import TrendMonitor
        monitor = TrendMonitor(
            interval_hours=args.monitor_interval,
            n_niches=args.hunt_niches,
            n_topics_per_niche=args.hunt_topics,
        )
        asyncio.run(monitor.run_forever())

    elif args.schedule:
        run_scheduler()

    elif args.batch:
        run_batch(Path(args.csv), upload=args.upload,
                  auto_schedule=args.auto_schedule,
                  default_profile=args.profile)

    elif args.topic:
        result = run_single(
            args.topic, args.tone, args.minutes,
            upload=args.upload,
            publish_at=args.publish_at,
            profile_id=args.profile,
        )
        if result["status"] == "done":
            print(f"\n{'═'*60}")
            print(f"✅  Video ready!")
            print(f"    Profile   : {result.get('profile')} ({result.get('market')} / {result.get('niche')})")
            print(f"    Title     : {result.get('title', '')}")
            print(f"    File      : {result.get('video_path', '')}")
            print(f"    Thumbnail : {result.get('thumb_path', '')}")
            if result.get("yt_id"):
                print(f"    YouTube   : https://youtu.be/{result['yt_id']}")
            print(f"{'═'*60}")
        else:
            print(f"\n❌  Failed: {result.get('error', 'unknown error')}")
            sys.exit(1)

    else:
        p.print_help()
