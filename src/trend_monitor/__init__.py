"""Trend Monitor package — multi-source opportunity discovery for dark YouTube channels."""
from .monitor import TrendMonitor
from .notebooklm_bridge import NotebookLMBridge
from .scorer import OpportunityScorer

__all__ = ["TrendMonitor", "NotebookLMBridge", "OpportunityScorer"]
