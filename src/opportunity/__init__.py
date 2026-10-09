"""
CineForge Opportunity Scanner — auto-discovery, scoring, storage, and notification.

Modules:
    database      — SQLite persistence for opportunities and run history
    scorer        — Gemini-powered 1-10 dark-content potential scorer
    notifier      — Telegram + Discord webhook notifications
    sheets_queue  — Append high-value topics to Google Sheets queue
    pipeline      — Orchestrator tying all four modules together
"""

from .database import OpportunityDB, ScoredOpportunity
from .scorer import DarkContentScorer
from .notifier import OpportunityNotifier
from .sheets_queue import SheetsQueue
from .pipeline import OpportunityScannerPipeline

__all__ = [
    "OpportunityDB",
    "ScoredOpportunity",
    "DarkContentScorer",
    "OpportunityNotifier",
    "SheetsQueue",
    "OpportunityScannerPipeline",
]
