"""
channel_hunter.py — Automatic YouTube channel opportunity discovery engine.

Architecture:
  1. TrendScout   — pulls real trending data from YouTube API v3 + Google Trends
  2. NicheAnalyser — uses GeminiNotebook to deep-analyse each niche
  3. OpportunityRanker — scores each niche by competition, CPM, content volume
  4. TopicGenerator — expands winning niches into specific video topics
  5. CSVWriter     — appends new topics to batch/topics.csv

Run as a script:
    python -m src.research.channel_hunter

Or call from code:
    from src.research.channel_hunter import ChannelHunter
    hunter = ChannelHunter()
    opportunities = await hunter.hunt(n_niches=10)
"""

from __future__ import annotations

import asyncio
import csv
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

# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class NicheOpportunity:
    """A discovered niche with scoring and candidate topics."""
    name: str
    category: str = ""
    description: str = ""
    score: float = 0.0           # 0–10: higher = better opportunity
    estimated_cpm_usd: float = 0.0
    competition_level: str = ""  # low / medium / high
    avg_monthly_views: int = 0
    top_channels: list[str] = field(default_factory=list)
    video_topics: list[dict] = field(default_factory=list)  # [{topic, tone, minutes}]
    sources: list[str] = field(default_factory=list)
    analysed_at: str = ""

    def to_csv_rows(self) -> list[dict]:
        """Convert candidate topics to topics.csv row format."""
        rows = []
        for t in self.video_topics:
            rows.append({
                "topic": t.get("topic", ""),
                "tone": t.get("tone", "suspense e mistério"),
                "minutes": str(t.get("minutes", 8)),
                "status": "",
                "youtube_id": "",
            })
        return rows


# ---------------------------------------------------------------------------
# TrendScout
# ---------------------------------------------------------------------------

class TrendScout:
    """
    Collects raw trend signals from multiple platforms:
      • YouTube Data API v3  — trending videos + category stats
      • YouTube Search       — niche keyword volumes (estimated)
      • Google Trends RSS    — rising search terms (no API key needed)
      • Reddit /r/nocode etc — community discussion signals
    """

    def __init__(self, youtube_api_key: str = "", region: str = "BR") -> None:
        self.yt_key = youtube_api_key or os.getenv("YOUTUBE_DATA_API_KEY", "")
        self.region = region
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/124 Safari/537.36"
            )
        })

    # ── YouTube trending ────────────────────────────────────────────────────

    def get_yt_trending(
        self, max_results: int = 50, category_id: str = "0"
    ) -> list[dict]:
        """
        Fetch YouTube trending videos for the configured region.
        Falls back to RSS feed if no API key is set.
        """
        if self.yt_key:
            return self._yt_api_trending(max_results, category_id)
        return self._yt_rss_trending(max_results)

    def _yt_api_trending(self, max_results: int, category_id: str) -> list[dict]:
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",
            "regionCode": self.region,
            "maxResults": min(max_results, 50),
            "key": self.yt_key,
        }
        if category_id != "0":
            params["videoCategoryId"] = category_id

        try:
            resp = self._session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            videos = []
            for item in items:
                snip = item.get("snippet", {})
                stats = item.get("statistics", {})
                videos.append({
                    "id": item.get("id", ""),
                    "title": snip.get("title", ""),
                    "channel": snip.get("channelTitle", ""),
                    "category": snip.get("categoryId", ""),
                    "description": snip.get("description", "")[:500],
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "tags": snip.get("tags", []),
                    "published": snip.get("publishedAt", ""),
                })
            log.info("YouTube API: %d trending videos fetched", len(videos))
            return videos
        except Exception as exc:
            log.warning("YouTube trending API failed: %s", exc)
            return []

    def _yt_rss_trending(self, max_results: int) -> list[dict]:
        """Scrape YouTube trending page as fallback (no API key)."""
        try:
            url = f"https://www.youtube.com/feed/trending?gl={self.region}"
            resp = self._session.get(url, timeout=15)
            # Parse initial data JSON embedded in page
            match = re.search(r"var ytInitialData\s*=\s*(\{.*?\});</script>", resp.text, re.DOTALL)
            if not match:
                return []
            data = json.loads(match.group(1))
            # Navigate to tabs[0].tabRenderer.content.sectionListRenderer.contents
            tabs = (data.get("contents", {})
                        .get("twoColumnBrowseResultsRenderer", {})
                        .get("tabs", []))
            videos: list[dict] = []
            for tab in tabs:
                sections = (tab.get("tabRenderer", {})
                                .get("content", {})
                                .get("sectionListRenderer", {})
                                .get("contents", []))
                for section in sections:
                    items = (section.get("itemSectionRenderer", {})
                                     .get("contents", []))
                    for item in items:
                        shelf = item.get("shelfRenderer", {})
                        for video_item in (shelf.get("content", {})
                                               .get("expandedShelfContentsRenderer", {})
                                               .get("items", [])):
                            vr = video_item.get("videoRenderer", {})
                            if vr:
                                videos.append({
                                    "id": vr.get("videoId", ""),
                                    "title": (vr.get("title", {})
                                                .get("runs", [{}])[0]
                                                .get("text", "")),
                                    "channel": (vr.get("ownerText", {})
                                                  .get("runs", [{}])[0]
                                                  .get("text", "")),
                                    "views": 0,
                                })
                            if len(videos) >= max_results:
                                break
            log.info("YouTube RSS: %d trending videos parsed", len(videos))
            return videos
        except Exception as exc:
            log.warning("YouTube RSS trending failed: %s", exc)
            return []

    # ── Google Trends RSS (no key) ──────────────────────────────────────────

    def get_google_trends(self, geo: str = "BR") -> list[str]:
        """Fetch daily trending searches from Google Trends RSS."""
        url = f"https://trends.google.com/trends/trendingsearches/daily/rss?geo={geo}"
        try:
            resp = self._session.get(url, timeout=12)
            resp.raise_for_status()
            titles = re.findall(r"<title>(.+?)</title>", resp.text)
            # Skip feed title (first item) and filter empty
            trends = [t.strip() for t in titles[1:] if t.strip() and len(t) > 3]
            log.info("Google Trends: %d trending searches for %s", len(trends), geo)
            return trends[:40]
        except Exception as exc:
            log.warning("Google Trends RSS failed: %s", exc)
            return []

    # ── YouTube Search (estimated volume via autocomplete) ─────────────────

    def get_search_suggestions(self, seed: str, lang: str = "pt") -> list[str]:
        """Use YouTube autocomplete to expand a seed keyword."""
        url = "https://suggestqueries.google.com/complete/search"
        params = {"client": "youtube", "ds": "yt", "q": seed, "hl": lang}
        try:
            resp = self._session.get(url, params=params, timeout=8)
            # Response is JSONP: window.google.ac.h([...])
            text = resp.text
            data = json.loads(text[text.index("["):text.rindex("]") + 1])
            suggestions = [item[0] for item in data[1] if isinstance(item, list)]
            return suggestions[:15]
        except Exception as exc:
            log.debug("Autocomplete failed for %r: %s", seed, exc)
            return []

    # ── SerpAPI / alternative SERP (optional) ─────────────────────────────

    def get_yt_search_results(
        self, query: str, max_results: int = 10, yt_api_key: str = ""
    ) -> list[dict]:
        """Use YouTube Data API to search for videos in a niche."""
        key = yt_api_key or self.yt_key
        if not key:
            return []
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount",
            "maxResults": min(max_results, 50),
            "regionCode": self.region,
            "key": key,
        }
        try:
            resp = requests.get(url, params=params, timeout=12)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            return [
                {
                    "id": i.get("id", {}).get("videoId", ""),
                    "title": i.get("snippet", {}).get("title", ""),
                    "channel": i.get("snippet", {}).get("channelTitle", ""),
                    "description": i.get("snippet", {}).get("description", "")[:300],
                }
                for i in items
            ]
        except Exception as exc:
            log.warning("YT search failed for %r: %s", query, exc)
            return []


# ---------------------------------------------------------------------------
# NicheAnalyser
# ---------------------------------------------------------------------------

class NicheAnalyser:
    """
    Uses GeminiNotebook to analyse a niche in depth:
    - Competition level
    - CPM estimates
    - Content gaps
    - Best video angles / topics
    """

    def __init__(self, gemini_api_key: str = "", use_grounding: bool = True) -> None:
        self._api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._use_grounding = use_grounding

    def analyse(
        self,
        niche_name: str,
        context_data: dict,
        n_topics: int = 10,
        language: str = "pt-BR",
    ) -> NicheOpportunity:
        """
        Deep-analyse a niche and return a scored NicheOpportunity.

        Parameters
        ----------
        niche_name : str
            Name of the niche to analyse (e.g. "crimes reais Brasil").
        context_data : dict
            Raw data from TrendScout to include as notebook sources.
        n_topics : int
            How many video topics to generate for this niche.
        language : str
            Language code for topic generation.
        """
        from .gemini_notebook import GeminiNotebook

        # Build context sources from scout data
        sources: list[str] = []

        # Add trending video titles as a text source
        yt_vids = context_data.get("yt_trending", [])
        if yt_vids:
            trending_text = "YOUTUBE TRENDING VIDEOS:\n" + "\n".join(
                f"- {v['title']} (channel: {v['channel']}, views: {v.get('views', 'N/A')})"
                for v in yt_vids[:20]
            )
            sources.append(trending_text)

        # Google Trends
        trends = context_data.get("google_trends", [])
        if trends:
            sources.append("GOOGLE TRENDS (daily):\n" + "\n".join(f"- {t}" for t in trends[:20]))

        # Autocomplete suggestions
        suggestions = context_data.get("suggestions", [])
        if suggestions:
            sources.append("SEARCH SUGGESTIONS:\n" + "\n".join(f"- {s}" for s in suggestions))

        nb = GeminiNotebook(
            sources=sources,
            title=f"Niche Analysis: {niche_name}",
            gemini_api_key=self._api_key,
            use_grounding=self._use_grounding,
        )

        # ── Query 1: Competition + CPM analysis ────────────────────────────
        analysis_result = nb.query(
            question=(
                f"Analyse the YouTube niche '{niche_name}' in detail. Provide:\n"
                f"1. Competition level (low/medium/high) and why\n"
                f"2. Estimated CPM range in USD\n"
                f"3. Average monthly views for channels in this niche\n"
                f"4. Key content gaps / underserved angles\n"
                f"5. Overall opportunity score from 0-10 with justification\n"
                f"6. Top 3-5 existing channels in this niche\n\n"
                f"Answer in JSON format with keys: competition_level, cpm_min, cpm_max, "
                f"avg_monthly_views, content_gaps, opportunity_score, top_channels, description\n"
            ),
            extra_instruction="Return ONLY valid JSON, no markdown fences.",
        )

        # Parse analysis JSON
        opp = NicheOpportunity(
            name=niche_name,
            analysed_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            raw = analysis_result.answer.strip()
            # Strip any accidental markdown
            if raw.startswith("```"):
                raw = re.sub(r"```\w*\n?", "", raw).strip()
            analysis_json = json.loads(raw)
            opp.competition_level = analysis_json.get("competition_level", "unknown")
            cpm_min = float(analysis_json.get("cpm_min", 0))
            cpm_max = float(analysis_json.get("cpm_max", 0))
            opp.estimated_cpm_usd = (cpm_min + cpm_max) / 2
            opp.avg_monthly_views = int(analysis_json.get("avg_monthly_views", 0))
            opp.score = float(analysis_json.get("opportunity_score", 5.0))
            opp.top_channels = analysis_json.get("top_channels", [])
            opp.description = analysis_json.get("description", "")
            opp.sources = [s.title for s in nb._sources]
        except (json.JSONDecodeError, ValueError, AttributeError) as exc:
            log.warning("Could not parse analysis JSON for %s: %s — raw: %s", niche_name, exc, analysis_result.answer[:200])
            # Fallback: store raw answer as description
            opp.description = analysis_result.answer[:500]
            opp.score = 5.0

        # ── Query 2: Video topic generation ───────────────────────────────
        topics_result = nb.query(
            question=(
                f"Generate {n_topics} specific, click-worthy video topics for the YouTube niche "
                f"'{niche_name}' in {language}. Each topic should be optimised for dark, dramatic, "
                f"crime, mystery, or suspense-style content that performs well in Brazil.\n\n"
                f"Return a JSON array where each item has:\n"
                f"  topic: (exact video title, in Portuguese, 60-80 chars, SEO optimised)\n"
                f"  tone: (e.g. 'suspense e mistério', 'terror e crime', 'investigativo')\n"
                f"  minutes: (integer, 8-15)\n"
                f"  hook: (first 5 seconds hook text in Portuguese)\n"
                f"  tags: (list of 5 YouTube tags)\n\n"
                f"Make topics maximally engaging — shocking facts, controversial angles, "
                f"untold stories, real crimes, mysteries. Return ONLY valid JSON array."
            ),
            extra_instruction="Return ONLY a valid JSON array, no markdown, no explanation.",
        )

        try:
            raw = topics_result.answer.strip()
            if raw.startswith("```"):
                raw = re.sub(r"```\w*\n?", "", raw).strip()
            opp.video_topics = json.loads(raw)
            log.info("Generated %d topics for niche: %s", len(opp.video_topics), niche_name)
        except (json.JSONDecodeError, ValueError) as exc:
            log.warning("Could not parse topics JSON for %s: %s", niche_name, exc)
            opp.video_topics = []

        return opp


# ---------------------------------------------------------------------------
# ChannelHunter — orchestrator
# ---------------------------------------------------------------------------

class ChannelHunter:
    """
    Main orchestrator that ties TrendScout + NicheAnalyser together.

    Usage:
        hunter = ChannelHunter()
        opportunities = await hunter.hunt(n_niches=5, n_topics_per_niche=8)
        hunter.save_to_csv(opportunities)
    """

    # Default seed niches by market (covers any niche type)
    SEED_NICHES_BY_MARKET = {
        "BR": [
            "crimes reais Brasil", "serial killers brasileiros",
            "casos policiais não resolvidos", "mistérios e conspirações",
            "histórias de terror real", "crimes famosos mundo",
            "paranormal e assombrado", "desaparecimentos misteriosos",
            "futebol brasileirão análise", "finanças pessoais investimentos",
            "tecnologia gadgets lançamentos", "saúde e bem-estar dicas",
            "educação curiosidades história", "receitas culinária brasileira",
            "notícias virais Brasil", "crianças educação infantil",
        ],
        "US": [
            "true crime USA unsolved", "serial killer cases America",
            "paranormal unexplained America", "conspiracy theories USA",
            "NFL football analysis", "NBA highlights analysis",
            "stock market investing tips", "real estate investing USA",
            "AI technology news", "health fitness tips USA",
            "history documentary USA", "cooking recipes American",
            "kids educational content", "science explained easy",
            "breaking news analysis", "personal finance budget",
        ],
        "GB": [
            "true crime UK unsolved", "British mysteries history",
            "Premier League football analysis", "UK politics explained",
            "British history documentary", "science technology UK",
            "personal finance UK investing", "health NHS tips",
            "cooking British recipes", "kids BBC educational",
        ],
        "FR": [
            "crimes réels France", "affaires criminelles non résolues",
            "mystères français histoire", "football Ligue 1 analyse",
            "finance investissement France", "technologie IA actualités",
            "santé bien-être conseils", "histoire de France documentaire",
            "cuisine recettes françaises", "actualités France analyse",
        ],
        "DE": [
            "wahre Verbrechen Deutschland", "Mysteries ungelöste Fälle DE",
            "Bundesliga Fußball Analyse", "Technologie KI Deutschland",
            "Finanzen Investieren Deutschland", "Geschichte Deutschland Doku",
            "Gesundheit Tipps Deutschland", "Kochen Rezepte Deutschland",
        ],
        "ES": [
            "crímenes reales España", "misterios sin resolver España",
            "fútbol La Liga análisis", "finanzas inversiones España",
            "tecnología IA noticias", "historia España documentales",
            "salud bienestar consejos", "cocina recetas españolas",
        ],
        "IT": [
            "crimini reali Italia", "misteri irrisolti Italia",
            "Serie A calcio analisi", "finanza investimenti Italia",
            "tecnologia IA notizie", "storia Italia documentari",
            "salute benessere consigli", "cucina ricette italiane",
        ],
    }

    # Backwards compat
    DARK_SEED_NICHES = SEED_NICHES_BY_MARKET["BR"]

    def __init__(
        self,
        gemini_api_key: str = "",
        youtube_api_key: str = "",
        region: str = "BR",
        language: str = "",
        use_grounding: bool = True,
    ) -> None:
        self._api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        self._yt_key = youtube_api_key or os.getenv("YOUTUBE_DATA_API_KEY", "")
        self._region = region.upper()
        self._language = language or self._detect_language(region)
        self._use_grounding = use_grounding
        self._scout = TrendScout(youtube_api_key=self._yt_key, region=self._region)
        self._analyser = NicheAnalyser(
            gemini_api_key=self._api_key, use_grounding=use_grounding
        )

    @staticmethod
    def _detect_language(region: str) -> str:
        mapping = {
            "BR": "pt-BR", "PT": "pt-PT",
            "US": "en-US", "GB": "en-GB", "AU": "en-AU", "CA": "en-CA",
            "FR": "fr-FR", "DE": "de-DE", "ES": "es-ES",
            "IT": "it-IT", "NL": "nl-NL", "PL": "pl-PL",
        }
        return mapping.get(region.upper(), "en-US")

    async def hunt(
        self,
        n_niches: int = 5,
        n_topics_per_niche: int = 8,
        extra_seed_niches: list[str] | None = None,
    ) -> list[NicheOpportunity]:
        """
        Full hunt: collect trends → analyse niches → return ranked opportunities.

        Parameters
        ----------
        n_niches : int
            How many niches to deeply analyse (costs 2 Gemini calls each).
        n_topics_per_niche : int
            Video topics to generate per winning niche.
        extra_seed_niches : list[str]
            Additional niche seeds to consider alongside defaults.

        Returns
        -------
        list[NicheOpportunity]
            Sorted by score descending.
        """
        log.info("=== ChannelHunter: starting hunt (niches=%d) ===", n_niches)

        # ── Step 1: Collect raw trend data ─────────────────────────────────
        log.info("[1/4] Collecting trend signals (region=%s, lang=%s)...", self._region, self._language)
        yt_trending = self._scout.get_yt_trending(max_results=50)
        google_trends = self._scout.get_google_trends(geo=self._region)

        # Use market-specific seeds
        market_seeds = self.SEED_NICHES_BY_MARKET.get(self._region, self.SEED_NICHES_BY_MARKET["US"])
        seeds = list(market_seeds)
        if extra_seed_niches:
            seeds = extra_seed_niches + seeds
        seeds = seeds[:n_niches * 3]  # keep pool 3× larger than needed

        # Expand each seed with autocomplete
        log.info("[2/4] Expanding seeds with autocomplete...")
        expanded_niches: list[str] = []
        for seed in seeds[:n_niches * 2]:
            expanded_niches.append(seed)
            suggestions = self._scout.get_search_suggestions(seed)
            expanded_niches.extend(suggestions[:2])
            time.sleep(0.3)  # be polite

        # Deduplicate and pick top n_niches
        seen: set[str] = set()
        unique_niches: list[str] = []
        for n in expanded_niches:
            key = n.lower().strip()
            if key not in seen:
                seen.add(key)
                unique_niches.append(n)
        niches_to_analyse = unique_niches[:n_niches]

        log.info("[3/4] Deep-analysing %d niches with Gemini...", len(niches_to_analyse))

        # ── Step 2: Analyse niches (can be parallelised but Gemini has rate limits) ──
        opportunities: list[NicheOpportunity] = []
        context_data = {
            "yt_trending": yt_trending,
            "google_trends": google_trends,
        }

        for i, niche in enumerate(niches_to_analyse, 1):
            log.info("  Analysing [%d/%d]: %s", i, len(niches_to_analyse), niche)
            # Add niche-specific suggestions
            context_data["suggestions"] = self._scout.get_search_suggestions(niche)
            try:
                opp = self._analyser.analyse(
                    niche_name=niche,
                    context_data=context_data,
                    n_topics=n_topics_per_niche,
                )
                opportunities.append(opp)
                log.info("    Score=%.1f  CPM=$%.2f  Competition=%s  Topics=%d",
                         opp.score, opp.estimated_cpm_usd,
                         opp.competition_level, len(opp.video_topics))
            except Exception as exc:
                log.error("  Failed to analyse %s: %s", niche, exc)

            # Rate limit: ~2 calls per niche, stay under 15 RPM free tier
            if i < len(niches_to_analyse):
                time.sleep(5)

        # ── Step 3: Rank ───────────────────────────────────────────────────
        log.info("[4/4] Ranking opportunities...")
        opportunities.sort(key=lambda o: o.score, reverse=True)

        for rank, opp in enumerate(opportunities, 1):
            log.info("  #%d %-40s  score=%.1f  cpm=$%.2f",
                     rank, opp.name[:40], opp.score, opp.estimated_cpm_usd)

        return opportunities

    def save_to_csv(
        self,
        opportunities: list[NicheOpportunity],
        csv_path: Path | None = None,
        append: bool = True,
    ) -> int:
        """
        Write video topics from all opportunities to topics.csv.

        Returns number of new rows added.
        """
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config.settings import BATCH_CSV

        csv_path = csv_path or BATCH_CSV
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing topics to avoid duplicates
        existing_topics: set[str] = set()
        if csv_path.exists():
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_topics.add(row.get("topic", "").lower().strip())

        new_rows: list[dict] = []
        for opp in opportunities:
            for row in opp.to_csv_rows():
                key = row["topic"].lower().strip()
                if key and key not in existing_topics:
                    new_rows.append(row)
                    existing_topics.add(key)

        if not new_rows:
            log.info("No new topics to add (all duplicates).")
            return 0

        fieldnames = ["topic", "tone", "minutes", "profile", "status", "youtube_id"]
        mode = "a" if (append and csv_path.exists()) else "w"
        write_header = not csv_path.exists() or mode == "w"

        # Ensure all rows have the profile field
        for row in new_rows:
            if "profile" not in row:
                row["profile"] = ""

        with csv_path.open(mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            writer.writerows(new_rows)

        log.info("Added %d new topics to %s", len(new_rows), csv_path)
        return len(new_rows)

    def save_report(
        self,
        opportunities: list[NicheOpportunity],
        output_dir: Path | None = None,
    ) -> Path:
        """Save full JSON report with all analysis data."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config.settings import OUTPUT

        output_dir = output_dir or (OUTPUT / "research_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = output_dir / f"channel_hunt_{ts}.json"

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_niches": len(opportunities),
            "total_topics": sum(len(o.video_topics) for o in opportunities),
            "opportunities": [
                {
                    "rank": i,
                    "name": o.name,
                    "score": o.score,
                    "competition": o.competition_level,
                    "cpm_usd": o.estimated_cpm_usd,
                    "avg_monthly_views": o.avg_monthly_views,
                    "description": o.description,
                    "top_channels": o.top_channels,
                    "video_topics": o.video_topics,
                    "sources": o.sources,
                    "analysed_at": o.analysed_at,
                }
                for i, o in enumerate(opportunities, 1)
            ],
        }

        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        log.info("Report saved to %s", report_path)
        return report_path


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

async def _main() -> None:
    import argparse
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.logger import setup_logging
    from config.settings import LOGS

    setup_logging(LOGS)
    log = logging.getLogger("channel_hunter")

    p = argparse.ArgumentParser(description="CineForge Channel Opportunity Hunter")
    p.add_argument("--niches", type=int, default=5, help="Number of niches to analyse (default 5)")
    p.add_argument("--topics", type=int, default=8, help="Topics per niche (default 8)")
    p.add_argument("--no-grounding", action="store_true", help="Disable Google Search grounding")
    p.add_argument("--extra-niches", nargs="*", help="Extra niche seeds to consider")
    p.add_argument("--dry-run", action="store_true", help="Don't write to topics.csv")
    args = p.parse_args()

    hunter = ChannelHunter(use_grounding=not args.no_grounding)
    opportunities = await hunter.hunt(
        n_niches=args.niches,
        n_topics_per_niche=args.topics,
        extra_seed_niches=args.extra_niches,
    )

    report_path = hunter.save_report(opportunities)
    print(f"\n{'═'*60}")
    print(f"CHANNEL HUNT COMPLETE")
    print(f"{'═'*60}")
    print(f"Niches analysed : {len(opportunities)}")
    print(f"Total topics    : {sum(len(o.video_topics) for o in opportunities)}")
    print(f"Full report     : {report_path}")
    print()
    print("TOP 3 OPPORTUNITIES:")
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"  #{i} {opp.name}")
        print(f"     Score: {opp.score:.1f}/10  |  CPM: ${opp.estimated_cpm_usd:.2f}  |  Competition: {opp.competition_level}")
        print(f"     Topics generated: {len(opp.video_topics)}")
    print()

    if not args.dry_run:
        n_added = hunter.save_to_csv(opportunities)
        print(f"Added {n_added} new topics to batch/topics.csv")
    else:
        print("[dry-run] topics.csv NOT modified")


if __name__ == "__main__":
    asyncio.run(_main())
