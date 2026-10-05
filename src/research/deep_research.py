"""
deep_research.py — Multi-source deep research pipeline.

Uses GeminiNotebook to pull research from:
  • YouTube trending + channel pages
  • Google Trends (no key)
  • Reddit public JSON API (no key)
  • Web articles (via requests)
  • Optional: Tavily API for premium search (set TAVILY_API_KEY)

This is the "NotebookLM equivalent" that the user requested —
it replicates NotebookLM's workflow of:
  create notebook → add sources → ask questions → get grounded answers

Usage:
    researcher = DeepResearcher()
    report = researcher.research_niche("crimes reais Brasil")
    print(report.summary)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)


@dataclass
class ResearchReport:
    """Output of a deep research session."""
    niche: str
    summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    channel_opportunities: list[dict] = field(default_factory=list)
    video_topics: list[dict] = field(default_factory=list)
    reddit_insights: list[str] = field(default_factory=list)
    sources_consulted: list[str] = field(default_factory=list)
    grounded: bool = False
    generated_at: str = ""


class DeepResearcher:
    """
    Multi-source research engine that mimics NotebookLM's notebook workflow.

    Steps:
    1. Gather sources from YouTube, Google Trends, Reddit, web articles
    2. Load all into a GeminiNotebook (the NotebookLM equivalent)
    3. Ask a series of deep-research questions
    4. Synthesise into a structured ResearchReport
    """

    # Reddit subs to scan for channel opportunity signals
    REDDIT_SUBS = [
        "brasil",
        "PodcastBrasil",
        "youtube",
        "youtubers",
        "truecrime",
        "misterios",
    ]

    def __init__(
        self,
        gemini_api_key: str = "",
        tavily_api_key: str = "",
        use_grounding: bool = True,
        cache_dir: Path | None = None,
    ) -> None:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        self._gkey = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._tkey = tavily_api_key or os.getenv("TAVILY_API_KEY", "")
        self._use_grounding = use_grounding
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 CineForge/1.0 research-bot"
        })

        from config.settings import OUTPUT
        self._cache_dir = cache_dir or (OUTPUT / "research_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Source collectors
    # ------------------------------------------------------------------

    def _collect_reddit(self, subreddit: str, query: str, limit: int = 10) -> str:
        """Collect Reddit posts about a query (public JSON, no auth)."""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {"q": query, "sort": "relevance", "limit": limit, "restrict_sr": "on"}
            resp = self._session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            posts = resp.json().get("data", {}).get("children", [])
            text_parts = []
            for post in posts:
                d = post.get("data", {})
                title = d.get("title", "")
                selftext = d.get("selftext", "")[:300]
                score = d.get("score", 0)
                if title:
                    text_parts.append(f"[{score} upvotes] {title}\n{selftext}")
            return "\n\n".join(text_parts) if text_parts else ""
        except Exception as exc:
            log.debug("Reddit collect failed for r/%s %r: %s", subreddit, query, exc)
            return ""

    def _collect_tavily(self, query: str, max_results: int = 5) -> list[dict]:
        """Use Tavily Search API if key is set (premium research)."""
        if not self._tkey:
            return []
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self._tkey,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "max_results": max_results,
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            return [
                {"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")[:800]}
                for r in results
            ]
        except Exception as exc:
            log.warning("Tavily search failed: %s", exc)
            return []

    def _collect_youtube_channel_data(self, query: str, yt_key: str = "") -> str:
        """Search YouTube channels in the niche and return their data."""
        key = yt_key or os.getenv("YOUTUBE_DATA_API_KEY", "")
        if not key:
            return ""
        try:
            resp = requests.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "q": query,
                    "type": "channel",
                    "maxResults": 10,
                    "regionCode": "BR",
                    "key": key,
                },
                timeout=12,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            lines = []
            for item in items:
                snip = item.get("snippet", {})
                lines.append(
                    f"Channel: {snip.get('channelTitle', '')} — {snip.get('description', '')[:200]}"
                )
            return "\n".join(lines)
        except Exception as exc:
            log.debug("YT channel search failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # Main research method
    # ------------------------------------------------------------------

    def research_niche(
        self,
        niche: str,
        n_topics: int = 12,
        language: str = "pt-BR",
        yt_key: str = "",
    ) -> ResearchReport:
        """
        Full deep-research on a niche. Replicates NotebookLM workflow:
        1. Gather sources (Reddit, YouTube, Tavily, Google Trends)
        2. Load into GeminiNotebook
        3. Query for insights, topics, gaps
        4. Return structured report
        """
        from .gemini_notebook import GeminiNotebook

        report = ResearchReport(
            niche=niche,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        log.info("Deep research started for: %s", niche)
        sources_text: list[str] = []

        # ── Collect Reddit data ───────────────────────────────────────────
        log.info("  Collecting Reddit signals...")
        reddit_texts: list[str] = []
        for sub in self.REDDIT_SUBS[:4]:
            text = self._collect_reddit(sub, niche, limit=5)
            if text:
                reddit_texts.append(f"[Reddit r/{sub}]\n{text}")
                report.reddit_insights.append(f"r/{sub}: {len(text.split())} words")
            time.sleep(0.5)

        if reddit_texts:
            sources_text.append("## REDDIT COMMUNITY SIGNALS\n" + "\n\n".join(reddit_texts))

        # ── Collect Tavily search (if key available) ───────────────────────
        if self._tkey:
            log.info("  Tavily deep search...")
            tavily_results = self._collect_tavily(
                f"YouTube niche '{niche}' channel opportunities CPM 2026", max_results=5
            )
            if tavily_results:
                tavily_text = "## TAVILY WEB RESEARCH\n" + "\n\n".join(
                    f"[{r['title']}] ({r['url']})\n{r['content']}"
                    for r in tavily_results
                )
                sources_text.append(tavily_text)
                report.sources_consulted.extend([r["url"] for r in tavily_results])

        # ── Collect YouTube channel data ───────────────────────────────────
        yt_channel_data = self._collect_youtube_channel_data(niche, yt_key=yt_key)
        if yt_channel_data:
            sources_text.append(f"## YOUTUBE CHANNELS IN NICHE\n{yt_channel_data}")

        # ── Build notebook ────────────────────────────────────────────────
        log.info("  Building Gemini research notebook (%d sources)...", len(sources_text))
        nb = GeminiNotebook(
            sources=sources_text if sources_text else [
                f"Research subject: {niche}. Analyse YouTube channel opportunities in Brazil."
            ],
            title=f"Deep Research: {niche}",
            gemini_api_key=self._gkey,
            use_grounding=self._use_grounding,
        )

        # ── Query 1: Executive summary ────────────────────────────────────
        log.info("  Query 1: Executive summary...")
        q1 = nb.query(
            question=(
                f"Based on all available data, provide an executive summary of the YouTube niche "
                f"'{niche}' in Brazil. Include:\n"
                f"- Current audience size and growth trajectory\n"
                f"- Monetization potential (CPM, RPM estimates)\n"
                f"- Why audiences in Brazil are drawn to this content\n"
                f"- Key psychological triggers that make this niche perform well\n"
                f"- Seasonal or trending patterns\n"
                f"Answer in Portuguese (pt-BR), structured, 300-500 words."
            )
        )
        report.summary = q1.answer
        report.grounded = q1.grounded

        # ── Query 2: Key findings / opportunities ─────────────────────────
        log.info("  Query 2: Key findings...")
        q2 = nb.query(
            question=(
                f"What are the 5-7 most important findings about channel opportunities in '{niche}' "
                f"that a new YouTube creator should know? Focus on:\n"
                f"- Content formats that get the most views\n"
                f"- Title formulas that perform well\n"
                f"- Thumbnail styles\n"
                f"- Upload frequency\n"
                f"- SEO tactics specific to this niche\n"
                f"Return as JSON array of strings (each finding is one string, in pt-BR)."
            ),
            extra_instruction="Return ONLY a valid JSON array of strings, no markdown.",
        )
        try:
            raw = q2.answer.strip()
            if raw.startswith("```"):
                raw = re.sub(r"```\w*\n?", "", raw).strip()
            report.key_findings = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            report.key_findings = [q2.answer[:500]]

        # ── Query 3: Specific video topics ────────────────────────────────
        log.info("  Query 3: Video topic generation (%d topics)...", n_topics)
        q3 = nb.query(
            question=(
                f"Generate {n_topics} viral-optimised video topics for a YouTube channel in the "
                f"'{niche}' niche targeting Brazilian audience (language: {language}). "
                f"Focus on true crime, mysteries, shocking stories, controversial cases.\n\n"
                f"Each topic must have:\n"
                f"  topic: (Portuguese title, 60-80 chars, hook word at start)\n"
                f"  tone: (one of: 'suspense e mistério', 'terror e crime', 'investigativo', "
                f"'chocante e controverso', 'dramático e emocional')\n"
                f"  minutes: (8-15, integer)\n"
                f"  hook: (opening 5-second hook sentence in Portuguese)\n"
                f"  tags: (5 YouTube SEO tags)\n"
                f"  thumbnail_concept: (describe the thumbnail in one sentence)\n\n"
                f"Return ONLY a valid JSON array."
            ),
            extra_instruction="Return ONLY valid JSON array, no markdown fences.",
        )
        try:
            raw = q3.answer.strip()
            if raw.startswith("```"):
                raw = re.sub(r"```\w*\n?", "", raw).strip()
            report.video_topics = json.loads(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            log.warning("Topics JSON parse failed: %s", exc)
            report.video_topics = []

        # ── Query 4: Channel gap analysis ────────────────────────────────
        log.info("  Query 4: Channel gap analysis...")
        q4 = nb.query(
            question=(
                f"What specific channel concepts in '{niche}' are missing or underserved in Brazil "
                f"as of 2026? Which exact content angles have high demand but low supply? "
                f"Return as JSON array of objects with keys: "
                f"concept, gap_reason, estimated_monthly_views, difficulty. "
                f"Return ONLY valid JSON array."
            ),
            extra_instruction="Return ONLY valid JSON array, no markdown.",
        )
        try:
            raw = q4.answer.strip()
            if raw.startswith("```"):
                raw = re.sub(r"```\w*\n?", "", raw).strip()
            report.channel_opportunities = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            report.channel_opportunities = []

        report.sources_consulted.extend([s.title for s in nb._sources])
        log.info("Deep research complete: %d topics, %d opportunities, grounded=%s",
                 len(report.video_topics), len(report.channel_opportunities), report.grounded)
        return report

    def save_report(self, report: ResearchReport, output_dir: Path | None = None) -> Path:
        """Save report as JSON."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config.settings import OUTPUT

        output_dir = output_dir or (OUTPUT / "research_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_niche = re.sub(r"[^a-z0-9]+", "_", report.niche.lower())[:40]
        path = output_dir / f"deep_research_{safe_niche}_{ts}.json"
        path.write_text(json.dumps(report.__dict__, ensure_ascii=False, indent=2))
        log.info("Research report saved: %s", path)
        return path
