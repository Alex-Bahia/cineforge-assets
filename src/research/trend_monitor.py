"""
trend_monitor.py — Continuous trend monitoring daemon.

Runs as a background service or scheduled job to continuously discover
new channel opportunities and feed them into the CineForge pipeline.

Architecture:
  • Polls YouTube RSS + Google Trends + Reddit every N hours
  • Passes new signals to DeepResearcher for Gemini analysis
  • Writes discovered topics directly to batch/topics.csv
  • Sends a summary notification log

Run:
    python -m src.research.trend_monitor --interval 12
    python -m src.research.trend_monitor --once
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)


class TrendMonitor:
    """
    Runs ChannelHunter on a schedule and feeds results into the pipeline.
    """

    def __init__(
        self,
        interval_hours: float = 12.0,
        n_niches: int = 3,
        n_topics_per_niche: int = 6,
        auto_add_to_queue: bool = True,
        gemini_api_key: str = "",
        use_grounding: bool = True,
    ) -> None:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        self._interval = interval_hours * 3600
        self._n_niches = n_niches
        self._n_topics = n_topics_per_niche
        self._auto_add = auto_add_to_queue
        self._gkey = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._use_grounding = use_grounding
        self._run_count = 0

    async def run_once(self) -> dict:
        """Execute one discovery cycle. Returns summary dict."""
        from .channel_hunter import ChannelHunter

        self._run_count += 1
        start = time.time()
        log.info("=== TrendMonitor run #%d ===", self._run_count)

        hunter = ChannelHunter(
            gemini_api_key=self._gkey,
            use_grounding=self._use_grounding,
        )
        opportunities = await hunter.hunt(
            n_niches=self._n_niches,
            n_topics_per_niche=self._n_topics,
        )

        report_path = hunter.save_report(opportunities)
        n_added = 0
        if self._auto_add and opportunities:
            n_added = hunter.save_to_csv(opportunities)

        elapsed = time.time() - start
        summary = {
            "run": self._run_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "niches_analysed": len(opportunities),
            "topics_generated": sum(len(o.video_topics) for o in opportunities),
            "topics_added_to_queue": n_added,
            "elapsed_seconds": round(elapsed, 1),
            "report": str(report_path),
            "top_opportunity": opportunities[0].name if opportunities else None,
        }

        log.info("Run #%d complete: %d niches, %d topics, +%d queued (%.0fs)",
                 self._run_count, summary["niches_analysed"],
                 summary["topics_generated"], n_added, elapsed)
        return summary

    async def run_forever(self) -> None:
        """Loop indefinitely, running one cycle every interval_hours."""
        log.info("TrendMonitor started: interval=%.1fh auto_queue=%s",
                 self._interval / 3600, self._auto_add)
        while True:
            try:
                await self.run_once()
            except Exception as exc:
                log.error("TrendMonitor cycle failed: %s", exc, exc_info=True)

            log.info("Next run in %.1f hours. Sleeping...", self._interval / 3600)
            await asyncio.sleep(self._interval)


# ── CLI ────────────────────────────────────────────────────────────────────────

async def _main() -> None:
    import argparse
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import setup_logging
    from config.settings import LOGS

    setup_logging(LOGS)

    p = argparse.ArgumentParser(description="CineForge Trend Monitor")
    p.add_argument("--interval", type=float, default=12.0,
                   help="Hours between discovery cycles (default 12)")
    p.add_argument("--once", action="store_true",
                   help="Run one cycle and exit")
    p.add_argument("--niches", type=int, default=3,
                   help="Niches to analyse per cycle (default 3)")
    p.add_argument("--topics", type=int, default=6,
                   help="Topics per niche (default 6)")
    p.add_argument("--no-auto-queue", action="store_true",
                   help="Don't add topics to batch/topics.csv automatically")
    p.add_argument("--no-grounding", action="store_true",
                   help="Disable Google Search grounding")
    args = p.parse_args()

    monitor = TrendMonitor(
        interval_hours=args.interval,
        n_niches=args.niches,
        n_topics_per_niche=args.topics,
        auto_add_to_queue=not args.no_auto_queue,
        use_grounding=not args.no_grounding,
    )

    if args.once:
        summary = await monitor.run_once()
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        await monitor.run_forever()


if __name__ == "__main__":
    asyncio.run(_main())
