"""
OpportunityDB — SQLite persistence layer for the opportunity scanner.

Schema:
    opportunities  — stores each scored opportunity (idempotent by url+topic hash)
    scan_runs      — audit log of every scanner invocation
    notifications  — tracks what was already notified (dedup)

All writes are wrapped in BEGIN/COMMIT; the file is safe for concurrent readers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Default DB location inside the project
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "batch" / "opportunities.db"


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class ScoredOpportunity:
    """One discovery record, as stored in SQLite."""
    topic: str
    source: str
    url: str = ""
    # Raw TrendMonitor score (0-100)
    raw_score: float = 0.0
    # Gemini AI score (1-10, dark-content potential)
    ai_score: float = 0.0
    # Final composite score: 0.5*raw_norm + 0.5*ai_score (re-normalised to 1-10)
    final_score: float = 0.0
    # Gemini reasoning for the score
    ai_reasoning: str = ""
    # Suggested video titles from Gemini
    title_variants: list[str] = field(default_factory=list)
    # Tags
    tags: list[str] = field(default_factory=list)
    # Metadata
    engagement_signal: int = 0
    keyword_match: int = 0
    recency_hours: float = 0.0
    # Timestamps
    discovered_at: str = ""   # ISO-8601 UTC
    notified: bool = False
    pushed_to_sheets: bool = False
    # Dedup key (sha256 of url|topic)
    opportunity_id: str = ""

    def __post_init__(self) -> None:
        if not self.discovered_at:
            self.discovered_at = datetime.now(timezone.utc).isoformat()
        if not self.opportunity_id:
            raw = f"{self.url}|{self.topic}"
            self.opportunity_id = hashlib.sha256(raw.encode()).hexdigest()[:16]


# ── Database class ────────────────────────────────────────────────────────────

class OpportunityDB:
    """Thread-safe SQLite wrapper for CineForge opportunities."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._init_schema()

    # ── Connection management ─────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")   # safe for concurrent reads
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS opportunities (
                opportunity_id   TEXT PRIMARY KEY,
                topic            TEXT NOT NULL,
                source           TEXT NOT NULL,
                url              TEXT DEFAULT '',
                raw_score        REAL DEFAULT 0,
                ai_score         REAL DEFAULT 0,
                final_score      REAL DEFAULT 0,
                ai_reasoning     TEXT DEFAULT '',
                title_variants   TEXT DEFAULT '[]',  -- JSON array
                tags             TEXT DEFAULT '[]',  -- JSON array
                engagement_signal INTEGER DEFAULT 0,
                keyword_match    INTEGER DEFAULT 0,
                recency_hours    REAL DEFAULT 0,
                discovered_at    TEXT NOT NULL,
                notified         INTEGER DEFAULT 0,
                pushed_to_sheets INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_opp_score ON opportunities(final_score DESC);
            CREATE INDEX IF NOT EXISTS idx_opp_notified ON opportunities(notified, final_score DESC);

            CREATE TABLE IF NOT EXISTS scan_runs (
                run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at   TEXT NOT NULL,
                finished_at  TEXT,
                total_found  INTEGER DEFAULT 0,
                high_value   INTEGER DEFAULT 0,  -- count with final_score >= 7
                status       TEXT DEFAULT 'running'
            );

            CREATE TABLE IF NOT EXISTS notifications (
                notification_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id   TEXT NOT NULL,
                channel          TEXT NOT NULL,  -- 'telegram' | 'discord'
                sent_at          TEXT NOT NULL,
                success          INTEGER DEFAULT 1
            );
            """)
        log.debug("[OpportunityDB] Schema ready at %s", self.db_path)

    # ── Write operations ──────────────────────────────────────────────────────

    def upsert(self, op: ScoredOpportunity) -> bool:
        """
        Insert or update one opportunity. Returns True if it was a new insert.
        Uses opportunity_id as the dedup key — safe to call repeatedly.
        """
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT opportunity_id FROM opportunities WHERE opportunity_id=?",
                (op.opportunity_id,),
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE opportunities SET
                        raw_score=?, ai_score=?, final_score=?,
                        ai_reasoning=?, title_variants=?, tags=?,
                        engagement_signal=?, keyword_match=?, recency_hours=?
                       WHERE opportunity_id=?""",
                    (
                        op.raw_score, op.ai_score, op.final_score,
                        op.ai_reasoning,
                        json.dumps(op.title_variants, ensure_ascii=False),
                        json.dumps(op.tags, ensure_ascii=False),
                        op.engagement_signal, op.keyword_match, op.recency_hours,
                        op.opportunity_id,
                    ),
                )
                return False
            else:
                conn.execute(
                    """INSERT INTO opportunities
                       (opportunity_id, topic, source, url,
                        raw_score, ai_score, final_score,
                        ai_reasoning, title_variants, tags,
                        engagement_signal, keyword_match, recency_hours,
                        discovered_at, notified, pushed_to_sheets)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        op.opportunity_id, op.topic, op.source, op.url,
                        op.raw_score, op.ai_score, op.final_score,
                        op.ai_reasoning,
                        json.dumps(op.title_variants, ensure_ascii=False),
                        json.dumps(op.tags, ensure_ascii=False),
                        op.engagement_signal, op.keyword_match, op.recency_hours,
                        op.discovered_at, int(op.notified), int(op.pushed_to_sheets),
                    ),
                )
                return True

    def mark_notified(self, opportunity_id: str, channel: str) -> None:
        """Mark an opportunity as notified and log the notification."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE opportunities SET notified=1 WHERE opportunity_id=?",
                (opportunity_id,),
            )
            conn.execute(
                "INSERT INTO notifications (opportunity_id, channel, sent_at) VALUES (?,?,?)",
                (opportunity_id, channel, datetime.now(timezone.utc).isoformat()),
            )

    def mark_pushed_to_sheets(self, opportunity_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE opportunities SET pushed_to_sheets=1 WHERE opportunity_id=?",
                (opportunity_id,),
            )

    def start_run(self) -> int:
        """Open a new scan_run record; returns run_id."""
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO scan_runs (started_at) VALUES (?)",
                (datetime.now(timezone.utc).isoformat(),),
            )
            return cur.lastrowid  # type: ignore[return-value]

    def finish_run(self, run_id: int, total: int, high_value: int, status: str = "ok") -> None:
        with self._connect() as conn:
            conn.execute(
                """UPDATE scan_runs SET
                    finished_at=?, total_found=?, high_value=?, status=?
                   WHERE run_id=?""",
                (datetime.now(timezone.utc).isoformat(), total, high_value, status, run_id),
            )

    # ── Read operations ───────────────────────────────────────────────────────

    def get_pending_notifications(self, min_score: float = 7.0) -> list[ScoredOpportunity]:
        """
        Return opportunities with final_score >= min_score that have not been notified yet.
        Sorted by final_score DESC.
        """
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM opportunities
                   WHERE notified=0 AND final_score >= ?
                   ORDER BY final_score DESC""",
                (min_score,),
            ).fetchall()
        return [self._row_to_op(r) for r in rows]

    def get_pending_sheets(self, min_score: float = 6.0) -> list[ScoredOpportunity]:
        """Return opportunities not yet pushed to Google Sheets."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM opportunities
                   WHERE pushed_to_sheets=0 AND final_score >= ?
                   ORDER BY final_score DESC""",
                (min_score,),
            ).fetchall()
        return [self._row_to_op(r) for r in rows]

    def get_top(self, n: int = 20, min_score: float = 0.0) -> list[ScoredOpportunity]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM opportunities
                   WHERE final_score >= ?
                   ORDER BY final_score DESC
                   LIMIT ?""",
                (min_score, n),
            ).fetchall()
        return [self._row_to_op(r) for r in rows]

    def total_count(self) -> int:
        with self._connect() as conn:
            return conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _row_to_op(row: sqlite3.Row) -> ScoredOpportunity:
        d = dict(row)
        d["title_variants"] = json.loads(d.get("title_variants") or "[]")
        d["tags"] = json.loads(d.get("tags") or "[]")
        d["notified"] = bool(d.get("notified", 0))
        d["pushed_to_sheets"] = bool(d.get("pushed_to_sheets", 0))
        return ScoredOpportunity(**{k: v for k, v in d.items() if k in ScoredOpportunity.__dataclass_fields__})

    def __repr__(self) -> str:
        return f"<OpportunityDB path={self.db_path} total={self.total_count()}>"
