"""
OpportunityScorer — computes a composite score for each Opportunity.

Score formula (0-100):
  - Recency         (30 pts)  — exponential decay, half-life 24h
  - Engagement      (30 pts)  — log-normalised view/upvote signal
  - Keyword match   (25 pts)  — count of dark seed keywords in title
  - Source weight   (15 pts)  — trust weight per source type

Higher score = stronger content opportunity.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .monitor import Opportunity

# Source trust weights (0.0 – 1.0)
SOURCE_WEIGHTS: dict[str, float] = {
    "youtube_trending": 1.0,    # highest: already trending on platform
    "serpapi_youtube": 0.95,
    "youtube_rss": 0.90,
    "google_news_rss": 0.85,
    "reddit": 0.80,
    "reddit_public": 0.75,
    "google_autocomplete": 0.60,  # lower: intent signal, not engagement
}

# Maximum expected engagement (used for log normalisation)
MAX_ENGAGEMENT = 10_000_000


class OpportunityScorer:
    """Stateless scorer — call .score(opportunity) to get a scored copy."""

    def score(self, op: "Opportunity") -> "Opportunity":
        recency_score = self._recency(op.recency_hours) * 30
        engagement_score = self._engagement(op.engagement_signal) * 30
        keyword_score = self._keyword(op.keyword_match) * 25
        source_score = self._source_weight(op.source) * 15

        op.score = round(recency_score + engagement_score + keyword_score + source_score, 2)
        return op

    # ── Component scorers (each returns 0.0–1.0) ────────────────────────────

    @staticmethod
    def _recency(hours: float) -> float:
        """Exponential decay with 24h half-life."""
        return math.exp(-0.693 * hours / 24.0)

    @staticmethod
    def _engagement(signal: int) -> float:
        """Log-normalised engagement: log10(signal+1) / log10(MAX+1)."""
        if signal <= 0:
            return 0.0
        return math.log10(signal + 1) / math.log10(MAX_ENGAGEMENT + 1)

    @staticmethod
    def _keyword(count: int) -> float:
        """Saturating keyword match: tanh(count/3)."""
        return math.tanh(count / 3.0)

    @staticmethod
    def _source_weight(source: str) -> float:
        for key, weight in SOURCE_WEIGHTS.items():
            if key in source:
                return weight
        return 0.5
