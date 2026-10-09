"""Trend Monitor package — multi-source opportunity discovery for dark YouTube channels."""
from .monitor import TrendMonitor
from .notebooklm_bridge import NotebookLMBridge
from .scorer import OpportunityScorer
from .kids_monitor import KidsOpportunityMonitor, KidsOpportunity
from .opportunity_router import OpportunityRouter, get_opportunity_router

__all__ = [
    "TrendMonitor",
    "NotebookLMBridge",
    "OpportunityScorer",
    "KidsOpportunityMonitor",
    "KidsOpportunity",
    "OpportunityRouter",
    "get_opportunity_router",
]
