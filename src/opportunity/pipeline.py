"""
OpportunityScannerPipeline — orchestrates the full opportunity discovery cycle:

    1. TrendMonitor scans all sources (YouTube, Reddit, RSS, SerpAPI, Autocomplete)
    2. DarkContentScorer scores each result via Gemini (1-10)
    3. OpportunityDB persists every result to SQLite (dedup by url+topic)
    4. OpportunityNotifier sends Telegram+Discord alerts for score >= NOTIFY_THRESHOLD
    5. SheetsQueue appends score >= SHEETS_THRESHOLD results to Google Sheets

All thresholds and behaviour are configurable via environment variables
or constructor parameters.

Standalone usage:
    pipeline = OpportunityScannerPipeline()
    summary = pipeline.run_once()
    print(summary)

Scheduled (24/7 with APScheduler):
    pipeline = OpportunityScannerPipeline()
    pipeline.start_scheduler(interval_minutes=90)   # blocks

Environment variables:
    OPPORTUNITY_NOTIFY_THRESHOLD   float, default 7.0  — minimum score to notify
    OPPORTUNITY_SHEETS_THRESHOLD   float, default 6.0  — minimum score for Sheets
    OPPORTUNITY_SCORE_TOP_N        int,   default 30   — how many to score per run
    OPPORTUNITY_SCHEDULER_INTERVAL int,   default 90   — scheduler interval (minutes)
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .database import OpportunityDB, ScoredOpportunity
from .scorer import DarkContentScorer
from .notifier import OpportunityNotifier
from .sheets_queue import SheetsQueue

log = logging.getLogger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────
NOTIFY_THRESHOLD  = float(os.getenv("OPPORTUNITY_NOTIFY_THRESHOLD", "7.0"))
SHEETS_THRESHOLD  = float(os.getenv("OPPORTUNITY_SHEETS_THRESHOLD", "6.0"))
SCORE_TOP_N       = int(os.getenv("OPPORTUNITY_SCORE_TOP_N", "30"))
SCHEDULER_INTERVAL = int(os.getenv("OPPORTUNITY_SCHEDULER_INTERVAL", "90"))


@dataclass
class RunSummary:
    """Result of one full pipeline run."""
    run_id: int = 0
    started_at: str = ""
    finished_at: str = ""
    duration_s: float = 0.0
    total_raw: int = 0           # opportunities from TrendMonitor
    total_scored: int = 0        # after Gemini scoring
    new_inserts: int = 0         # newly inserted into DB
    high_value: int = 0          # final_score >= NOTIFY_THRESHOLD
    notifications_sent: int = 0  # Telegram + Discord combined
    sheets_pushed: int = 0       # appended to Google Sheets
    errors: list[str] = None     # type: ignore[assignment]

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def __str__(self) -> str:
        return (
            f"RunSummary(run_id={self.run_id}, duration={self.duration_s:.0f}s, "
            f"raw={self.total_raw}, scored={self.total_scored}, "
            f"new={self.new_inserts}, high_value={self.high_value}, "
            f"notified={self.notifications_sent}, sheets={self.sheets_pushed})"
        )


class OpportunityScannerPipeline:
    """
    Full-cycle opportunity scanner.

    Args:
        db_path:               SQLite file path (default: batch/opportunities.db)
        notify_threshold:      Minimum final_score to trigger notification (default: 7.0)
        sheets_threshold:      Minimum final_score to push to Google Sheets (default: 6.0)
        score_top_n:           How many TrendMonitor results to Gemini-score per run
        gemini_api_key:        Google AI key (defaults to GEMINI_API_KEY env var)
        telegram_token:        Telegram bot token (defaults to TELEGRAM_BOT_TOKEN)
        telegram_chat_id:      Telegram chat id (defaults to TELEGRAM_CHAT_ID)
        discord_webhook_url:   Discord webhook URL (defaults to DISCORD_WEBHOOK_URL)
        sheets_creds_path:     Path to service account JSON (defaults to config/sheets_creds.json)
        spreadsheet_id:        Google Sheets ID (defaults to GOOGLE_SHEETS_ID)
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        notify_threshold: float = NOTIFY_THRESHOLD,
        sheets_threshold: float = SHEETS_THRESHOLD,
        score_top_n: int = SCORE_TOP_N,
        gemini_api_key: Optional[str] = None,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None,
        sheets_creds_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
    ) -> None:
        self.notify_threshold = notify_threshold
        self.sheets_threshold = sheets_threshold
        self.score_top_n = score_top_n

        self.db = OpportunityDB(db_path) if db_path else OpportunityDB()
        self.scorer = DarkContentScorer(api_key=gemini_api_key)
        self.notifier = OpportunityNotifier(
            telegram_token=telegram_token,
            telegram_chat_id=telegram_chat_id,
            discord_webhook_url=discord_webhook_url,
        )
        self.sheets = SheetsQueue(
            creds_path=sheets_creds_path,
            spreadsheet_id=spreadsheet_id,
        )

        log.info(
            "[Pipeline] Initialised — notify_threshold=%.1f  sheets_threshold=%.1f  "
            "score_top_n=%d",
            self.notify_threshold, self.sheets_threshold, self.score_top_n,
        )

    # ── Main run ──────────────────────────────────────────────────────────────

    def run_once(self) -> RunSummary:
        """Execute one full scan → score → store → notify → sheets cycle."""
        summary = RunSummary(started_at=datetime.now(timezone.utc).isoformat())
        run_id = self.db.start_run()
        summary.run_id = run_id
        t0 = time.time()

        # ── Step 1: Collect trend signals ─────────────────────────────────────
        log.info("[Pipeline] Step 1 — collecting trend signals …")
        raw_opportunities = self._collect_trends()
        summary.total_raw = len(raw_opportunities)
        log.info("[Pipeline] Collected %d raw opportunities.", summary.total_raw)

        if not raw_opportunities:
            log.warning("[Pipeline] No opportunities found — check API keys.")
            self.db.finish_run(run_id, 0, 0, "no_results")
            summary.finished_at = datetime.now(timezone.utc).isoformat()
            summary.duration_s = time.time() - t0
            return summary

        # ── Step 2: Convert to ScoredOpportunity and Gemini-score ─────────────
        log.info("[Pipeline] Step 2 — scoring top %d with Gemini …", self.score_top_n)
        scored_ops = self._score_opportunities(raw_opportunities[: self.score_top_n])
        summary.total_scored = len(scored_ops)

        # ── Step 3: Persist to SQLite ─────────────────────────────────────────
        log.info("[Pipeline] Step 3 — persisting to SQLite …")
        for op in scored_ops:
            is_new = self.db.upsert(op)
            if is_new:
                summary.new_inserts += 1

        high_value_ops = [op for op in scored_ops if op.final_score >= self.notify_threshold]
        summary.high_value = len(high_value_ops)
        log.info(
            "[Pipeline] Inserted %d new, %d high-value (score ≥ %.1f).",
            summary.new_inserts, summary.high_value, self.notify_threshold,
        )

        # ── Step 4: Notify for high-value results ─────────────────────────────
        log.info("[Pipeline] Step 4 — sending notifications …")
        pending_notify = self.db.get_pending_notifications(self.notify_threshold)
        notified_count = 0
        for op in pending_notify:
            results = self.notifier.notify(op)
            any_sent = any(results.values())
            if any_sent:
                channel_name = "telegram" if results.get("telegram") else "discord"
                self.db.mark_notified(op.opportunity_id, channel_name)
                notified_count += 1
        summary.notifications_sent = notified_count
        log.info("[Pipeline] Sent %d notifications.", notified_count)

        # ── Step 5: Push to Google Sheets ─────────────────────────────────────
        log.info("[Pipeline] Step 5 — pushing to Google Sheets …")
        pending_sheets = self.db.get_pending_sheets(self.sheets_threshold)
        if pending_sheets:
            ok, fail = self.sheets.push_batch(pending_sheets)
            for op in pending_sheets[:ok]:
                self.db.mark_pushed_to_sheets(op.opportunity_id)
            summary.sheets_pushed = ok
            log.info("[Pipeline] Pushed %d rows to Sheets (%d failed).", ok, fail)

        # ── Finish ────────────────────────────────────────────────────────────
        summary.finished_at = datetime.now(timezone.utc).isoformat()
        summary.duration_s = time.time() - t0
        self.db.finish_run(run_id, summary.total_scored, summary.high_value)

        # Send scan summary notification
        self.notifier.send_summary(
            total_found=summary.total_raw,
            high_value=summary.high_value,
            run_duration_s=summary.duration_s,
        )

        log.info("[Pipeline] Run complete: %s", summary)
        return summary

    # ── Scheduler ─────────────────────────────────────────────────────────────

    def start_scheduler(
        self,
        interval_minutes: int = SCHEDULER_INTERVAL,
        run_immediately: bool = True,
    ) -> None:
        """
        Start APScheduler-based 24/7 monitoring loop.
        Blocks the calling thread until KeyboardInterrupt.

        Requires: pip install apscheduler
        """
        try:
            from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore
            from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
        except ImportError:
            log.error(
                "[Pipeline] apscheduler not installed. "
                "Run: pip install 'apscheduler>=3.10'"
            )
            raise

        scheduler = BlockingScheduler(timezone="UTC")
        scheduler.add_job(
            self._scheduled_run,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="opportunity_scan",
            name="CineForge Opportunity Scanner",
            misfire_grace_time=60,       # allow up to 60s late start
            coalesce=True,               # skip missed fires (don't pile up)
            max_instances=1,             # no concurrent runs
        )

        log.info(
            "[Pipeline] Scheduler starting — interval=%d min. Press Ctrl+C to stop.",
            interval_minutes,
        )

        if run_immediately:
            log.info("[Pipeline] Running first scan immediately …")
            self._scheduled_run()

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            log.info("[Pipeline] Scheduler stopped.")

    def _scheduled_run(self) -> None:
        """Wrapper for scheduler — catches exceptions so the job keeps running."""
        try:
            summary = self.run_once()
            log.info("[Pipeline/Scheduler] %s", summary)
        except Exception as exc:
            log.exception("[Pipeline/Scheduler] Unhandled error: %s", exc)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _collect_trends(self) -> list:
        """Import and run TrendMonitor; returns list[Opportunity] sorted by score desc."""
        try:
            from src.trend_monitor import TrendMonitor  # type: ignore
        except ImportError:
            log.error("[Pipeline] Could not import TrendMonitor from src.trend_monitor.")
            return []

        try:
            monitor = TrendMonitor()
            return monitor.run()
        except Exception as exc:
            log.exception("[Pipeline] TrendMonitor.run() failed: %s", exc)
            return []

    def _score_opportunities(self, raw_ops: list) -> list[ScoredOpportunity]:
        """
        Convert TrendMonitor Opportunity objects → ScoredOpportunity and score them.
        """
        scored = []
        for raw_op in raw_ops:
            # Build ScoredOpportunity from the TrendMonitor Opportunity dataclass
            op = ScoredOpportunity(
                topic=getattr(raw_op, "topic", str(raw_op)),
                source=getattr(raw_op, "source", "unknown"),
                url=getattr(raw_op, "url", ""),
                raw_score=float(getattr(raw_op, "score", 0)),
                engagement_signal=int(getattr(raw_op, "engagement_signal", 0)),
                keyword_match=int(getattr(raw_op, "keyword_match", 0)),
                recency_hours=float(getattr(raw_op, "recency_hours", 0)),
                tags=list(getattr(raw_op, "tags", [])),
            )
            scored.append(op)

        # Score batch with Gemini (with 0.5s delay between calls)
        return self.scorer.score_batch(scored, delay=0.5)
