"""CineForge Research Module — channel opportunity discovery + Gemini RAG pipeline."""

from .channel_monitor import (  # noqa: F401
    ChannelMonitor,
    ChannelVideo,
    ContentOpportunity,
    RSSSubscriber,
    ViralDetector,
    PatternExtractor,
    OpportunityScorer,
    DARK_BR_CHANNELS,
)
from .gemini_notebook import GeminiNotebook, NotebookResult  # noqa: F401
from .channel_hunter import ChannelHunter, NicheOpportunity  # noqa: F401
