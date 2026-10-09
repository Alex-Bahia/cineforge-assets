#!/usr/bin/env python3
"""
test_research.py — Quick validation of the research pipeline.

Runs a minimal end-to-end test without consuming heavy Gemini quota.
Tests: imports, TrendScout (no API key needed), GeminiNotebook init.

Usage:
    python test_research.py
    python test_research.py --full   # Full Gemini call (needs GEMINI_API_KEY)
"""

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("test_research")


def test_imports() -> bool:
    log.info("Testing module imports...")
    try:
        from src.research.gemini_notebook import GeminiNotebook, NotebookResult
        from src.research.channel_hunter import ChannelHunter, TrendScout, NicheAnalyser
        from src.research.deep_research import DeepResearcher
        from src.research.trend_monitor import TrendMonitor
        log.info("  ✓ All research modules imported successfully")
        return True
    except ImportError as exc:
        log.error("  ✗ Import failed: %s", exc)
        return False


def test_trend_scout() -> bool:
    log.info("Testing TrendScout (Google Trends RSS — no API key)...")
    try:
        from src.research.channel_hunter import TrendScout
        scout = TrendScout(region="BR")
        trends = scout.get_google_trends(geo="BR")
        log.info("  ✓ Google Trends: %d trending searches fetched", len(trends))
        if trends:
            log.info("    Top 3: %s", ", ".join(trends[:3]))
        return True
    except Exception as exc:
        log.warning("  ✗ TrendScout failed: %s (needs network access)", exc)
        return False


def test_autocomplete() -> bool:
    log.info("Testing YouTube autocomplete suggestions...")
    try:
        from src.research.channel_hunter import TrendScout
        scout = TrendScout()
        suggestions = scout.get_search_suggestions("crimes reais brasil")
        log.info("  ✓ Got %d autocomplete suggestions", len(suggestions))
        if suggestions:
            log.info("    e.g.: %s", suggestions[0])
        return True
    except Exception as exc:
        log.warning("  ✗ Autocomplete failed: %s", exc)
        return False


def test_gemini_notebook(api_key: str = "") -> bool:
    log.info("Testing GeminiNotebook (requires GEMINI_API_KEY)...")
    try:
        from src.research.gemini_notebook import GeminiNotebook
        nb = GeminiNotebook(
            sources=["Crimes reais no Brasil são um nicho de YouTube muito lucrativo."],
            title="Test Notebook",
            gemini_api_key=api_key,
            use_grounding=True,
        )
        result = nb.query("What are dark YouTube channel niches in Brazil? Answer in 2 sentences.")
        log.info("  ✓ GeminiNotebook query successful")
        log.info("    Answer preview: %s", result.answer[:200])
        log.info("    Grounded: %s, Citations: %d", result.grounded, len(result.citations))
        return True
    except Exception as exc:
        log.error("  ✗ GeminiNotebook failed: %s", exc)
        return False


def test_channel_hunter_dry(api_key: str = "") -> bool:
    log.info("Testing ChannelHunter (1 niche, dry run)...")
    try:
        import asyncio
        from src.research.channel_hunter import ChannelHunter

        hunter = ChannelHunter(gemini_api_key=api_key, use_grounding=True)
        opportunities = asyncio.run(hunter.hunt(n_niches=1, n_topics_per_niche=3))
        log.info("  ✓ ChannelHunter: %d opportunities", len(opportunities))
        if opportunities:
            opp = opportunities[0]
            log.info("    Top niche: %s (score=%.1f, topics=%d)",
                     opp.name, opp.score, len(opp.video_topics))
        return True
    except Exception as exc:
        log.error("  ✗ ChannelHunter failed: %s", exc)
        return False


def main() -> None:
    p = argparse.ArgumentParser(description="Test CineForge research pipeline")
    p.add_argument("--full", action="store_true",
                   help="Run full Gemini tests (requires GEMINI_API_KEY)")
    p.add_argument("--api-key", default="",
                   help="Gemini API key (overrides .env)")
    args = p.parse_args()

    print("\n" + "═" * 60)
    print("CineForge Research Pipeline — Validation")
    print("═" * 60)

    results = {
        "imports": test_imports(),
        "trend_scout": test_trend_scout(),
        "autocomplete": test_autocomplete(),
    }

    if args.full:
        api_key = args.api_key
        if not api_key:
            from dotenv import load_dotenv
            import os
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY", "")

        if api_key:
            results["gemini_notebook"] = test_gemini_notebook(api_key)
            results["channel_hunter"] = test_channel_hunter_dry(api_key)
        else:
            log.warning("Skipping Gemini tests — GEMINI_API_KEY not set")

    print("\n" + "═" * 60)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    for name, ok in results.items():
        print(f"  {'✓' if ok else '✗'} {name}")
    print("═" * 60)
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
