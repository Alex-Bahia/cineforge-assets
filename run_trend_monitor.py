#!/usr/bin/env python3
"""
CineForge — Trend Monitor CLI
==============================
Automatically discovers new dark YouTube channel opportunities from 5+ sources
and optionally enriches them with NotebookLM / Gemini deep research.

Quick start:
    python run_trend_monitor.py

With NotebookLM enrichment on top results:
    python run_trend_monitor.py --enrich --top 5

Inject directly into pipeline batch:
    python run_trend_monitor.py --push-to-batch

Schedule (runs every 6 hours, adds new topics to batch/topics.csv):
    python run_trend_monitor.py --schedule

Environment variables (.env):
    YOUTUBE_API_KEY         YouTube Data API v3 key (free, 10k quota/day)
    REDDIT_CLIENT_ID        Reddit app client ID (free)
    REDDIT_CLIENT_SECRET    Reddit app client secret
    SERPAPI_KEY             SerpAPI key (250 free searches/month)
    GEMINI_API_KEY          Google AI Studio key (already used by pipeline)
    NOTEBOOKLM_NOTEBOOK_ID  Optional: notebook ID to push sources into

Getting free API keys:
    YouTube:  https://console.cloud.google.com → YouTube Data API v3
    Reddit:   https://www.reddit.com/prefs/apps → create "script" app
    SerpAPI:  https://serpapi.com/users/sign_up (250 free/month)
"""

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from src.utils.logger import setup_logging
from config.settings import LOGS

setup_logging(LOGS)
log = logging.getLogger("cineforge.trend_monitor")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CineForge Trend Monitor — multi-source dark topic discovery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--top", type=int, default=20,
        help="Number of top opportunities to show / export (default: 20)",
    )
    p.add_argument(
        "--enrich", action="store_true",
        help="Enrich top N results with NotebookLM/Gemini deep research",
    )
    p.add_argument(
        "--enrich-top", type=int, default=5,
        help="How many top results to enrich with deep research (default: 5)",
    )
    p.add_argument(
        "--push-to-batch", action="store_true",
        help="Append top results to batch/topics.csv for the pipeline",
    )
    p.add_argument(
        "--json-out", type=str, default="",
        help="Save full JSON report to this path (default: auto-named in batch/)",
    )
    p.add_argument(
        "--schedule", action="store_true",
        help="Run every 6 hours continuously, pushing to batch/topics.csv",
    )
    p.add_argument(
        "--interval-hours", type=float, default=6.0,
        help="Interval between scheduled runs in hours (default: 6)",
    )
    p.add_argument(
        "--no-notebooklm-mcp", action="store_true",
        help="Skip notebooklm-mcp and use Gemini API directly for enrichment",
    )
    p.add_argument(
        "--monitor", action="store_true",
        help=(
            "Run ChannelMonitor: subscribe to competitor RSS feeds, detect viral "
            "videos, score opportunities and auto-enrich with Gemini. "
            "Results appended to batch/topics.csv and saved to research_cache/."
        ),
    )
    p.add_argument(
        "--monitor-window", type=int, default=168,
        help="ChannelMonitor scan window in hours (default: 168 = 7 days)",
    )
    p.add_argument(
        "--viral-threshold", type=float, default=4.0,
        help="ChannelMonitor: minimum viral score 0–10 (default: 4.0)",
    )
    return p.parse_args()


def run_once(args: argparse.Namespace) -> list:
    from src.trend_monitor import TrendMonitor, NotebookLMBridge

    log.info("=" * 60)
    log.info("CineForge Trend Monitor starting …")

    monitor = TrendMonitor()
    opportunities = monitor.run()

    if not opportunities:
        log.warning("No opportunities found. Check API keys and network.")
        return []

    print(f"\n{'='*60}")
    print(f"  TOP {min(args.top, len(opportunities))} OPPORTUNITIES")
    print(f"{'='*60}")
    for i, op in enumerate(opportunities[: args.top], 1):
        print(f"\n{i:2}. [{op.score:5.1f}] {op.topic[:70]}")
        print(f"     Source: {op.source} | Engagement: {op.engagement_signal:,} | "
              f"Keywords: {op.keyword_match} | Recency: {op.recency_hours:.0f}h ago")
        if op.url:
            print(f"     URL: {op.url[:80]}")

    # ── Deep Research enrichment ──────────────────────────────────────────────
    if args.enrich:
        use_mcp = not args.no_notebooklm_mcp
        bridge = NotebookLMBridge(use_notebooklm_mcp=use_mcp)
        print(f"\n{'='*60}")
        print(f"  DEEP RESEARCH (top {args.enrich_top})")
        print(f"{'='*60}")

        for op in opportunities[: args.enrich_top]:
            print(f"\nResearching: {op.topic[:60]} …")
            research = bridge.research_opportunity(op.topic)

            print(f"  Refined topic : {research.refined_topic}")
            print(f"  Confidence    : {research.confidence:.0%}")
            if research.title_variants:
                print("  Title variants:")
                for t in research.title_variants[:5]:
                    print(f"    • {t}")
            if research.narrative_outline:
                print("  Narrative outline:")
                for n in research.narrative_outline[:4]:
                    print(f"    - {n}")
            if research.thumbnail_concept:
                print(f"  Thumbnail     : {research.thumbnail_concept[:100]}")

            # Attach research to opportunity so it's saved in JSON
            op.suggested_title_pt = research.refined_topic
            if research.title_variants:
                op.tags = (research.youtube_tags + op.tags)[:15]

        # Add discovered URLs as sources to NotebookLM notebook
        source_urls = [op.url for op in opportunities[:args.enrich_top] if op.url]
        if source_urls and not args.no_notebooklm_mcp:
            bridge.add_sources_to_notebook(source_urls)

    # ── Export ────────────────────────────────────────────────────────────────
    if args.push_to_batch:
        csv_path = monitor.export_to_csv(opportunities, top_n=args.top)
        print(f"\nExported to batch CSV: {csv_path}")

    json_out = Path(args.json_out) if args.json_out else None
    saved = monitor.export_to_json(opportunities[:args.top], json_path=json_out)
    print(f"Full report saved: {saved}")

    return opportunities


def run_scheduled(args: argparse.Namespace) -> None:
    import schedule
    import time

    interval_h = args.interval_hours

    def job():
        log.info("Scheduled trend scan starting …")
        args.push_to_batch = True
        run_once(args)

    schedule.every(interval_h).hours.do(job)
    log.info("Trend Monitor scheduled every %.1f hours. Running first scan now …", interval_h)
    job()  # run immediately

    while True:
        schedule.run_pending()
        time.sleep(60)


def run_monitor(args: argparse.Namespace) -> dict:
    """Run ChannelMonitor: RSS feed scan + viral detection + opportunity scoring."""
    from src.research.channel_monitor import ChannelMonitor  # type: ignore[import]

    log.info("=" * 60)
    log.info("CineForge ChannelMonitor starting …")

    monitor = ChannelMonitor(
        newer_than_hours=args.monitor_window,
        viral_threshold=args.viral_threshold,
    )
    report = monitor.scan()

    print(f"\n{'='*65}")
    print(f"  CHANNEL MONITOR REPORT  —  {report['generated_at'][:10]}")
    print(f"{'='*65}")
    print(f"  Channels monitored : {report['channels_monitored']}")
    print(f"  Videos found       : {report['videos_found']}")
    print(f"  Viral detected     : {report['viral_videos']}")
    print(f"  Opportunities      : {len(report['opportunities'])}")

    if report["top_keywords"]:
        print("\n  TOP KEYWORDS:")
        for entry in report["top_keywords"][:12]:
            print(f"    [{entry['count']:>3}x]  {entry['kw']}")

    if report["opportunities"]:
        print(f"\n  TOP {min(args.top, len(report['opportunities']))} OPPORTUNITIES:")
        for i, opp in enumerate(report["opportunities"][:args.top], 1):
            print(f"\n  {i:2}. [{opp['opportunity_score']:.1f}/10]  {opp['topic']}")
            print(f"      Source: {opp['channel_source']}  |  Competition: {opp['competition']}")
            if opp.get("title_hooks"):
                print(f"      Best title: {opp['title_hooks'][0]}")
            if opp.get("key_keywords"):
                print(f"      Keywords: {', '.join(opp['key_keywords'][:5])}")

    print(f"\n  Report saved → research_cache/channel_monitor_report.json")
    print(f"{'='*65}")
    return report


def main() -> None:
    args = parse_args()

    if args.monitor:
        run_monitor(args)
    elif args.schedule:
        run_scheduled(args)
    else:
        run_once(args)


if __name__ == "__main__":
    main()
