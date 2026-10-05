"""
SheetsQueue — appends high-value opportunities to a Google Sheets topics queue.

The spreadsheet acts as the human review layer: the pipeline operator can
glance at the sheet, mark rows as "approved" or "skip", and the pipeline
picks them up from there.

Sheet columns (appended to the first empty row):
    A  opportunity_id   — dedup key
    B  final_score      — composite 1-10 score
    C  ai_score         — Gemini score
    D  topic            — raw topic string
    E  suggested_title  — first title variant from Gemini (if any)
    F  source           — origin (youtube_trending, reddit, etc.)
    G  url              — source URL
    H  tags             — comma-separated tags
    I  ai_reasoning     — why this score
    J  discovered_at    — ISO-8601 UTC timestamp
    K  status           — always "pending" when first added

Setup (one-time):
    1. Create a Google Cloud service account:
       console.cloud.google.com → IAM → Service Accounts → Create
    2. Enable the Google Sheets API for your project
    3. Download the JSON credentials → save as config/sheets_creds.json
       (or set GOOGLE_SHEETS_CREDS_JSON env var to the file path)
    4. Create a Google Sheet and share it with the service account email
       (e.g. my-sa@my-project.iam.gserviceaccount.com) as Editor
    5. Copy the spreadsheet ID from the URL:
       https://docs.google.com/spreadsheets/d/<SPREADSHEET_ID>/edit
       Set GOOGLE_SHEETS_ID env var

Alternatively, use GOOGLE_SHEETS_NAME (sheet name) to let gspread find it.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .database import ScoredOpportunity

log = logging.getLogger(__name__)

# Default credentials path
DEFAULT_CREDS = Path(__file__).parent.parent.parent / "config" / "sheets_creds.json"

# Header row — written once when the sheet is empty
HEADER_ROW = [
    "opportunity_id", "final_score", "ai_score", "topic",
    "suggested_title", "source", "url", "tags",
    "ai_reasoning", "discovered_at", "status",
]


class SheetsQueue:
    """
    Appends scored opportunities to a Google Sheets spreadsheet.

    Usage:
        queue = SheetsQueue()
        pushed = queue.push(op)   # returns True if successfully appended
        queue.push_batch(ops)
    """

    def __init__(
        self,
        creds_path: Optional[str | Path] = None,
        spreadsheet_id: Optional[str] = None,
        spreadsheet_name: Optional[str] = None,
        worksheet_name: str = "Opportunities",
    ) -> None:
        self.creds_path = Path(creds_path or os.getenv("GOOGLE_SHEETS_CREDS_JSON", DEFAULT_CREDS))
        self.spreadsheet_id = spreadsheet_id or os.getenv("GOOGLE_SHEETS_ID", "")
        self.spreadsheet_name = spreadsheet_name or os.getenv("GOOGLE_SHEETS_NAME", "CineForge Opportunities")
        self.worksheet_name = worksheet_name

        self._gc = None       # gspread client
        self._ws = None       # active worksheet
        self._ready = False

        self._ready = self._init()

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init(self) -> bool:
        try:
            import gspread  # type: ignore
            from google.oauth2.service_account import Credentials  # type: ignore
        except ImportError:
            log.warning(
                "[SheetsQueue] gspread or google-auth not installed. "
                "Run: pip install gspread google-auth"
            )
            return False

        if not self.creds_path.exists():
            log.warning(
                "[SheetsQueue] Credentials file not found at %s. "
                "Set GOOGLE_SHEETS_CREDS_JSON or place sheets_creds.json in config/.",
                self.creds_path,
            )
            return False

        try:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(str(self.creds_path), scopes=scopes)
            self._gc = gspread.authorize(creds)  # type: ignore[attr-defined]

            # Open spreadsheet by ID (preferred) or by name
            if self.spreadsheet_id:
                ss = self._gc.open_by_key(self.spreadsheet_id)
            else:
                ss = self._gc.open(self.spreadsheet_name)

            # Get or create the worksheet
            try:
                self._ws = ss.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:  # type: ignore[attr-defined]
                self._ws = ss.add_worksheet(
                    title=self.worksheet_name, rows=1000, cols=len(HEADER_ROW)
                )
                self._ws.append_row(HEADER_ROW)
                log.info("[SheetsQueue] Created worksheet '%s'.", self.worksheet_name)

            # Ensure header row exists
            existing = self._ws.row_values(1)
            if not existing:
                self._ws.append_row(HEADER_ROW)

            log.info("[SheetsQueue] Connected to Google Sheets '%s'.", self.worksheet_name)
            return True

        except Exception as exc:
            log.warning("[SheetsQueue] Initialisation failed: %s", exc)
            return False

    # ── Public API ────────────────────────────────────────────────────────────

    def push(self, op: "ScoredOpportunity") -> bool:
        """
        Append one opportunity as a new row in the Google Sheet.
        Returns True on success.
        """
        if not self._ready or self._ws is None:
            log.debug("[SheetsQueue] Not ready — skipping push for '%s'.", op.topic[:50])
            return False

        row = self._op_to_row(op)
        try:
            self._ws.append_row(row, value_input_option="USER_ENTERED")
            log.info("[SheetsQueue] Pushed '%s' (score %.1f).", op.topic[:60], op.final_score)
            return True
        except Exception as exc:
            log.warning("[SheetsQueue] append_row failed: %s", exc)
            return False

    def push_batch(
        self,
        opportunities: list["ScoredOpportunity"],
    ) -> tuple[int, int]:
        """
        Push multiple opportunities. Returns (success_count, fail_count).
        Uses batch append for efficiency (one API call per 50 rows).
        """
        if not self._ready or self._ws is None:
            return 0, len(opportunities)

        rows = [self._op_to_row(op) for op in opportunities]
        try:
            # gspread append_rows sends all rows in one API call
            self._ws.append_rows(rows, value_input_option="USER_ENTERED")
            log.info("[SheetsQueue] Batch pushed %d rows.", len(rows))
            return len(rows), 0
        except Exception as exc:
            log.warning("[SheetsQueue] batch push failed (%s) — falling back to one-by-one.", exc)
            success = 0
            fail = 0
            for op in opportunities:
                if self.push(op):
                    success += 1
                else:
                    fail += 1
            return success, fail

    @property
    def is_ready(self) -> bool:
        return self._ready

    # ── Row serialiser ────────────────────────────────────────────────────────

    @staticmethod
    def _op_to_row(op: "ScoredOpportunity") -> list:
        suggested_title = op.title_variants[0] if op.title_variants else ""
        tags_str = ", ".join(op.tags[:10])
        return [
            op.opportunity_id,
            round(op.final_score, 2),
            round(op.ai_score, 2),
            op.topic,
            suggested_title,
            op.source,
            op.url,
            tags_str,
            op.ai_reasoning[:500] if op.ai_reasoning else "",
            op.discovered_at,
            "pending",
        ]
