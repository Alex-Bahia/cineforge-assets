#!/usr/bin/env python3
"""
CineForge — Opportunity Scanner CLI
=====================================
Automatically discovers, scores, and delivers new dark-content channel
opportunities from multiple sources (YouTube, Reddit, RSS, SerpAPI).

Quick start (single scan):
    python run_opportunity_scanner.py

Continuous 24/7 monitoring (every 90 minutes):
    python run_opportunity_scanner.py --schedule

Custom interval (every 2 hours):
    python run_opportunity_scanner.py --schedule --interval 120

Show DB stats:
    python run_opportunity_scanner.py --stats

Required environment variables (.env):
    GEMINI_API_KEY              Google AI Studio key (free tier)
    TELEGRAM_BOT_TOKEN          From @BotFather on Telegram
    TELEGRAM_CHAT_ID            Your personal or group chat ID
    DISCORD_WEBHOOK_URL         Discord channel webhook URL (optional)
    GOOGLE_SHEETS_ID            Spreadsheet ID from URL (optional)
    GOOGLE_SHEETS_CREDS_JSON    Path to service-account JSON (optional)
    YOUTUBE_API_KEY             YouTube Data API v3 key (optional)
    SERPAPI_KEY                 SerpAPI key for YouTube trends (optional)

Telegram setup (5 minutes):
    1. Message @BotFather → /newbot
    2. Pick a name and username for your bot
    3. Copy the bot token → TELEGRAM_BOT_TOKEN
    4. Message your bot to get a chat_id
       or use: https://api.telegram.org/bot<TOKEN>/getUpdates
    5. Set TELEGRAM_CHAT_ID to the numeric id (e.g. 123456789 or -1001234567890)

Install dependencies:
    pip install apscheduler python-telegram-bot requests gspread google-auth

APScheduler docs: https://apscheduler.readthedocs.io/en/stable/
"""

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from src.utils.logger import setup_logging
from config.settings import LOGS

setup_logging(LOGS)
log = logging.getLogger("cineforge.opportunity_scanner")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CineForge Opportunity Scanner — dark-content channel discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--schedule", action="store_true",
        help="Run continuously on a fixed interval (use --interval to set minutes)",
    )
    p.add_argument(
        "--interval", type=int, default=90,
        help="Scheduler interval in minutes when --schedule is set (default: 90)",
    )
    p.add_argument(
        "--notify-threshold", type=float, default=7.0,
        help="Minimum score (1-10) to trigger Telegram/Discord notification (default: 7.0)",
    )
    p.add_argument(
        "--sheets-threshold", type=float, default=6.0,
        help="Minimum score (1-10) to push to Google Sheets queue (default: 6.0)",
    )
    p.add_argument(
        "--top-n", type=int, default=30,
        help="Number of TrendMonitor results to Gemini-score per run (default: 30)",
    )
    p.add_argument(
        "--stats", action="store_true",
        help="Print database statistics and exit",
    )
    p.add_argument(
        "--no-notify", action="store_true",
        help="Disable Telegram/Discord notifications for this run",
    )
    p.add_argument(
        "--no-sheets", action="store_true",
        help="Disable Google Sheets push for this run",
    )
    return p.parse_args()


def show_stats() -> None:
    """Print current database statistics."""
    from src.opportunity import OpportunityDB

    db = OpportunityDB()
    total = db.total_count()
    top20 = db.get_top(20, min_score=5.0)

    print(f"\n{'='*60}")
    print(f"  CINEFORGE OPPORTUNITY DATABASE STATS")
    print(f"{'='*60}")
    print(f"  Total opportunities stored: {total}")
    print(f"  High-value (≥7): {len([o for o in db.get_top(9999, 7.0)])}")
    print(f"  DB path: {db.db_path}")

    if top20:
        print(f"\n  TOP 20 OPPORTUNITIES (score ≥ 5.0):")
        print(f"  {'SCORE':>5}  {'AI':>4}  {'SOURCE':<20}  TOPIC")
        print(f"  {'─'*5}  {'─'*4}  {'─'*20}  {'─'*40}")
        for op in top20:
            score_bar = "█" * round(op.final_score) + "░" * (10 - round(op.final_score))
            print(
                f"  {op.final_score:>5.1f}  "
                f"{op.ai_score:>4.1f}  "
                f"{op.source[:20]:<20}  "
                f"{op.topic[:50]}"
            )
    print()


def build_pipeline(args: argparse.Namespace):
    """Construct OpportunityScannerPipeline with optional overrides."""
    from src.opportunity import OpportunityScannerPipeline

    kwargs = {
        "notify_threshold": args.notify_threshold,
        "sheets_threshold": args.sheets_threshold,
        "score_top_n": args.top_n,
    }

    if args.no_notify:
        kwargs["telegram_token"] = "__disabled__"
        kwargs["discord_webhook_url"] = "__disabled__"

    if args.no_sheets:
        kwargs["sheets_creds_path"] = "__disabled__"

    return OpportunityScannerPipeline(**kwargs)


def main() -> None:
    args = parse_args()

    if args.stats:
        show_stats()
        return

    print("\n" + "=" * 60)
    print("  CINEFORGE OPPORTUNITY SCANNER")
    print("=" * 60)
    print(f"  Notify threshold : ≥ {args.notify_threshold}")
    print(f"  Sheets threshold : ≥ {args.sheets_threshold}")
    print(f"  Score top N      : {args.top_n} per run")
    if args.schedule:
        print(f"  Scheduler        : every {args.interval} minutes (24/7)")
    print("=" * 60 + "\n")

    pipeline = build_pipeline(args)

    if args.schedule:
        pipeline.start_scheduler(
            interval_minutes=args.interval,
            run_immediately=True,
        )
    else:
        summary = pipeline.run_once()
        print("\n" + "=" * 60)
        print(f"  SCAN COMPLETE")
        print("=" * 60)
        print(f"  Duration       : {summary.duration_s:.0f}s")
        print(f"  Raw found      : {summary.total_raw}")
        print(f"  Scored         : {summary.total_scored}")
        print(f"  New inserts    : {summary.new_inserts}")
        print(f"  High value ≥{args.notify_threshold:.0f} : {summary.high_value}")
        print(f"  Notified       : {summary.notifications_sent}")
        print(f"  Sheets pushed  : {summary.sheets_pushed}")
        if summary.errors:
            print(f"  Errors         : {len(summary.errors)}")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
