"""
TrendMonitor — multi-source dark-content opportunity scanner for Brazilian YouTube.

Sources polled (all free or free-tier):
  1. YouTube Data API v3  — mostPopular chart, regionCode=BR  (1 quota unit each)
  2. Google Autocomplete  — suggestqueries endpoint, no key needed
  3. Reddit PRAW          — r/brasil, r/relacionamentos, r/desabafos, r/TIFU
  4. Google News RSS      — feedparser, crime/dark topic queries
  5. YouTube RSS          — channel-level RSS feeds (no quota cost)
  6. SerpAPI              — YouTube search + Google Trends (250 free/month)

Usage:
    from src.trend_monitor import TrendMonitor

    monitor = TrendMonitor()
    results = monitor.run()          # returns list[Opportunity] sorted by score desc
    monitor.export_to_csv(results)   # appends to batch/topics.csv for the pipeline
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import time
import urllib.parse
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp
import feedparser
import requests

log = logging.getLogger(__name__)

# ── Dark/crime seed keywords for Brazil ──────────────────────────────────────
DARK_SEEDS_PT = [
    "crime real",
    "serial killer brasil",
    "assassinato misterioso",
    "caso não resolvido",
    "psicopata",
    "mistério policial",
    "crime chocante",
    "morte suspeita",
    "sequestro brasil",
    "tragédia brasileira",
    "caso perturbador",
    "desaparecimento inexplicável",
    "crime bizarro",
    "esquema criminoso",
    "golpe milionário",
    "fraude financeira",
    "morte acidental suspeita",
    "suicídio famoso",
    "acidente não foi acidente",
    "verdade oculta",
]

DARK_SEEDS_EN = [
    "true crime brazil",
    "unsolved murder brazil",
    "serial killer brazil",
    "dark mystery brazil",
    "crime documentary brazil",
]

REDDIT_SUBREDDITS = [
    "brasil",
    "relacionamentos",
    "desabafos",
    "TIFU",
    "conspiracaobr",
    "noticias",
    "policialbr",
]

GOOGLE_NEWS_TOPICS = [
    "crime+brasil",
    "assassinato+brasil",
    "caso+policial+brasil",
    "mistério+brasil",
    "tragédia+brasil",
    "serial+killer+brasil",
]

# YouTube channels to monitor via RSS (add your competitor channels)
COMPETITOR_CHANNELS = [
    # Each entry: channel_id, friendly_name
    # Add real channel IDs here; these are illustrative stubs
    # ("UCxxxxxxxxxxxxxxxxxxxxxxxx", "Canal Crimes Reais BR"),
]


@dataclass
class Opportunity:
    """A ranked content opportunity."""
    topic: str
    source: str
    score: float = 0.0
    engagement_signal: int = 0    # views / upvotes / comments raw
    recency_hours: float = 72.0   # how recent (lower = fresher)
    keyword_match: int = 0        # dark seed keywords found in title/body
    url: str = ""
    raw_title: str = ""
    suggested_title_pt: str = ""
    tags: list[str] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TrendMonitor:
    """
    Polls 5+ sources and returns scored Opportunity objects for the pipeline.

    All network I/O is async where possible; synchronous fallbacks are provided
    for environments without a running event loop.
    """

    def __init__(
        self,
        youtube_api_key: str | None = None,
        reddit_client_id: str | None = None,
        reddit_client_secret: str | None = None,
        reddit_user_agent: str = "cineforge-trend-monitor/1.0",
        serpapi_key: str | None = None,
        region_code: str = "BR",
        language: str = "pt",
        max_results_per_source: int = 25,
        output_dir: Path | None = None,
    ):
        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY", "")
        self.reddit_client_id = reddit_client_id or os.getenv("REDDIT_CLIENT_ID", "")
        self.reddit_client_secret = reddit_client_secret or os.getenv("REDDIT_CLIENT_SECRET", "")
        self.reddit_user_agent = reddit_user_agent
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY", "")
        self.region_code = region_code
        self.language = language
        self.max_results = max_results_per_source

        # Resolve output dir relative to project root
        root = Path(__file__).parent.parent.parent
        self.output_dir = output_dir or (root / "batch")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._scorer = OpportunityScorer()

    # ──────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────────

    def run(self) -> list[Opportunity]:
        """
        Synchronous entry point — runs all sources, deduplicates, scores and
        returns opportunities sorted by score descending.
        """
        try:
            loop = asyncio.get_running_loop()
            # Already inside an event loop (Jupyter / FastAPI); schedule coroutine
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(asyncio.run, self._run_async())
                return future.result()
        except RuntimeError:
            return asyncio.run(self._run_async())

    async def _run_async(self) -> list[Opportunity]:
        """Async implementation — polls all sources concurrently."""
        log.info("[TrendMonitor] Starting multi-source poll …")
        tasks = [
            self._fetch_youtube_trending(),
            self._fetch_google_autocomplete(),
            self._fetch_reddit(),
            self._fetch_google_news_rss(),
            self._fetch_youtube_rss_channels(),
        ]
        if self.serpapi_key:
            tasks.append(self._fetch_serpapi_youtube())

        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        raw: list[Opportunity] = []
        source_names = [
            "youtube_trending", "google_autocomplete", "reddit",
            "google_news_rss", "youtube_rss", "serpapi",
        ]
        for name, result in zip(source_names, gathered):
            if isinstance(result, Exception):
                log.warning("[%s] Error: %s", name, result)
            else:
                raw.extend(result)
                log.info("[%s] Found %d raw opportunities", name, len(result))

        deduped = self._deduplicate(raw)
        scored = [self._scorer.score(op) for op in deduped]
        scored.sort(key=lambda o: o.score, reverse=True)
        log.info("[TrendMonitor] Done. %d unique opportunities after dedup.", len(scored))
        return scored

    def export_to_csv(
        self,
        opportunities: list[Opportunity],
        csv_path: Path | None = None,
        top_n: int = 20,
    ) -> Path:
        """
        Append top_n opportunities to batch/topics.csv (used by run_pipeline.py).
        Returns the path written.
        """
        csv_path = csv_path or (self.output_dir / "topics.csv")
        fieldnames = ["topic", "tone", "duration_min", "source", "score", "url", "status"]

        # Read existing topics to avoid duplicate entries
        existing: set[str] = set()
        if csv_path.exists():
            with open(csv_path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    existing.add(row.get("topic", "").strip().lower())

        new_rows = []
        for op in opportunities[:top_n]:
            if op.topic.lower() not in existing:
                new_rows.append({
                    "topic": op.topic,
                    "tone": "suspense e mistério",
                    "duration_min": 8,
                    "source": op.source,
                    "score": round(op.score, 2),
                    "url": op.url,
                    "status": "pending",
                })
                existing.add(op.topic.lower())

        write_header = not csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(new_rows)

        log.info("Exported %d new opportunities to %s", len(new_rows), csv_path)
        return csv_path

    def export_to_json(
        self,
        opportunities: list[Opportunity],
        json_path: Path | None = None,
    ) -> Path:
        """Save full opportunity list (with all metadata) as JSON."""
        json_path = json_path or (
            self.output_dir / f"trends_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        data = [asdict(op) for op in opportunities]
        json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        log.info("Full trend report saved to %s", json_path)
        return json_path

    # ──────────────────────────────────────────────────────────────────────────
    # SOURCE 1: YouTube Data API v3 — mostPopular chart
    # Quota cost: videos.list with chart=mostPopular = 1 unit
    # (NOT search.list which costs 100 units per call)
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_youtube_trending(self) -> list[Opportunity]:
        if not self.youtube_api_key:
            log.warning("[youtube_trending] No YOUTUBE_API_KEY — skipping.")
            return []

        # videoCategoryId=25 (News & Politics) and 27 (Education) are good for dark content
        # We fetch all categories and filter by title keyword match
        base_url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "key": self.youtube_api_key,
            "part": "snippet,statistics,contentDetails",
            "chart": "mostPopular",        # <- 1 quota unit (NOT search which = 100)
            "regionCode": self.region_code,
            "maxResults": 50,              # max per call
            "hl": self.language,
        }

        opportunities = []
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as resp:
                if resp.status != 200:
                    log.warning("[youtube_trending] HTTP %d", resp.status)
                    return []
                data = await resp.json()

        for item in data.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            view_count = int(stats.get("viewCount", 0))
            like_count = int(stats.get("likeCount", 0))
            comment_count = int(stats.get("commentCount", 0))
            video_id = item.get("id", "")
            published = snippet.get("publishedAt", "")

            # Dark keyword filter
            kw_score = _count_dark_keywords(title + " " + description)
            if kw_score == 0:
                continue  # Skip non-dark content

            recency_h = _hours_since(published)
            opportunities.append(Opportunity(
                topic=_clean_topic(title),
                source="youtube_trending",
                engagement_signal=view_count + like_count * 50 + comment_count * 10,
                recency_hours=recency_h,
                keyword_match=kw_score,
                url=f"https://www.youtube.com/watch?v={video_id}",
                raw_title=title,
                tags=snippet.get("tags", [])[:10],
            ))

        log.info("[youtube_trending] %d dark items found", len(opportunities))
        return opportunities

    # ──────────────────────────────────────────────────────────────────────────
    # SOURCE 2: Google Autocomplete — free, no key needed
    # Expands each dark seed with a-z suffix to get 200-400 long-tail per seed
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_google_autocomplete(self) -> list[Opportunity]:
        BASE = "https://suggestqueries.google.com/complete/search"
        seen: set[str] = set()
        opportunities = []

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for seed in DARK_SEEDS_PT[:8]:   # limit to avoid rate limit
                # Direct seed query
                params = {
                    "client": "firefox",
                    "q": seed,
                    "hl": "pt-BR",
                    "gl": "BR",
                }
                try:
                    async with session.get(BASE, params=params, timeout=aiohttp.ClientTimeout(total=5)) as r:
                        if r.status == 200:
                            payload = await r.json(content_type=None)
                            suggestions = payload[1] if len(payload) > 1 else []
                            for sug in suggestions:
                                if sug not in seen:
                                    seen.add(sug)
                                    kw = _count_dark_keywords(sug)
                                    if kw > 0:
                                        opportunities.append(Opportunity(
                                            topic=_clean_topic(sug),
                                            source="google_autocomplete",
                                            recency_hours=24.0,  # autocomplete = fresh signal
                                            keyword_match=kw,
                                            raw_title=sug,
                                        ))
                    await asyncio.sleep(0.3)  # polite delay
                except Exception as exc:
                    log.debug("[google_autocomplete] seed '%s' error: %s", seed, exc)

        log.info("[google_autocomplete] %d suggestions", len(opportunities))
        return opportunities

    # ──────────────────────────────────────────────────────────────────────────
    # SOURCE 3: Reddit PRAW — hot/top posts from dark subreddits
    # Free: 100 req/min average; PRAW handles auth + rate limiting
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_reddit(self) -> list[Opportunity]:
        if not self.reddit_client_id or not self.reddit_client_secret:
            log.warning("[reddit] No REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET — using public endpoint.")
            return await self._fetch_reddit_public()

        try:
            import praw  # type: ignore
        except ImportError:
            log.warning("[reddit] praw not installed — pip install praw")
            return await self._fetch_reddit_public()

        reddit = praw.Reddit(
            client_id=self.reddit_client_id,
            client_secret=self.reddit_client_secret,
            user_agent=self.reddit_user_agent,
        )

        opportunities = []
        for sub_name in REDDIT_SUBREDDITS:
            try:
                sub = reddit.subreddit(sub_name)
                for post in sub.hot(limit=self.max_results):
                    kw = _count_dark_keywords(post.title + " " + (post.selftext or ""))
                    if kw == 0:
                        continue
                    created_h = (time.time() - post.created_utc) / 3600
                    opportunities.append(Opportunity(
                        topic=_clean_topic(post.title),
                        source=f"reddit/r/{sub_name}",
                        engagement_signal=post.score + post.num_comments * 5,
                        recency_hours=created_h,
                        keyword_match=kw,
                        url=f"https://reddit.com{post.permalink}",
                        raw_title=post.title,
                    ))
            except Exception as exc:
                log.warning("[reddit] r/%s error: %s", sub_name, exc)

        log.info("[reddit] %d dark posts", len(opportunities))
        return opportunities

    async def _fetch_reddit_public(self) -> list[Opportunity]:
        """Fallback: use Reddit's public JSON API (no auth, 60 req/min)."""
        opportunities = []
        headers = {"User-Agent": self.reddit_user_agent}

        async with aiohttp.ClientSession(headers=headers) as session:
            for sub_name in REDDIT_SUBREDDITS[:4]:
                url = f"https://www.reddit.com/r/{sub_name}/hot.json?limit={self.max_results}"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                    posts = data.get("data", {}).get("children", [])
                    for post_wrap in posts:
                        post = post_wrap.get("data", {})
                        title = post.get("title", "")
                        selftext = post.get("selftext", "")
                        kw = _count_dark_keywords(title + " " + selftext)
                        if kw == 0:
                            continue
                        created_h = (time.time() - post.get("created_utc", time.time())) / 3600
                        score = post.get("score", 0)
                        comments = post.get("num_comments", 0)
                        opportunities.append(Opportunity(
                            topic=_clean_topic(title),
                            source=f"reddit_public/r/{sub_name}",
                            engagement_signal=score + comments * 5,
                            recency_hours=created_h,
                            keyword_match=kw,
                            url=f"https://reddit.com{post.get('permalink', '')}",
                            raw_title=title,
                        ))
                    await asyncio.sleep(1.0)
                except Exception as exc:
                    log.debug("[reddit_public] r/%s error: %s", sub_name, exc)

        log.info("[reddit_public] %d dark posts", len(opportunities))
        return opportunities

    # ──────────────────────────────────────────────────────────────────────────
    # SOURCE 4: Google News RSS — free, no key, returns ~100 items per query
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_google_news_rss(self) -> list[Opportunity]:
        opportunities = []
        base = "https://news.google.com/rss/search"

        async with aiohttp.ClientSession() as session:
            for topic_query in GOOGLE_NEWS_TOPICS:
                params = {
                    "q": topic_query,
                    "hl": "pt-BR",
                    "gl": "BR",
                    "ceid": "BR:pt-419",
                }
                url = f"{base}?{urllib.parse.urlencode(params)}"
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status != 200:
                            continue
                        xml_text = await resp.text()
                    feed = feedparser.parse(xml_text)
                    for entry in feed.entries[:15]:
                        title = entry.get("title", "")
                        link = entry.get("link", "")
                        published = entry.get("published", "")
                        kw = _count_dark_keywords(title)
                        if kw == 0:
                            continue
                        recency_h = _hours_since(published) if published else 48.0
                        opportunities.append(Opportunity(
                            topic=_clean_topic(title),
                            source="google_news_rss",
                            recency_hours=recency_h,
                            keyword_match=kw,
                            url=link,
                            raw_title=title,
                        ))
                    await asyncio.sleep(0.5)
                except Exception as exc:
                    log.debug("[google_news_rss] query '%s' error: %s", topic_query, exc)

        log.info("[google_news_rss] %d dark articles", len(opportunities))
        return opportunities

    # ──────────────────────────────────────────────────────────────────────────
    # SOURCE 5: YouTube Channel RSS — free, no API key needed
    # Each channel exposes: https://www.youtube.com/feeds/videos.xml?channel_id=ID
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_youtube_rss_channels(self) -> list[Opportunity]:
        if not COMPETITOR_CHANNELS:
            log.info("[youtube_rss] No competitor channels configured — skipping.")
            return []

        opportunities = []
        async with aiohttp.ClientSession() as session:
            for channel_id, friendly_name in COMPETITOR_CHANNELS:
                url = (
                    f"https://www.youtube.com/feeds/videos.xml"
                    f"?channel_id={channel_id}"
                )
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                        if resp.status != 200:
                            continue
                        xml = await resp.text()
                    feed = feedparser.parse(xml)
                    for entry in feed.entries[:15]:
                        title = entry.get("title", "")
                        link = entry.get("link", "")
                        published = entry.get("published", "")
                        kw = _count_dark_keywords(title)
                        recency_h = _hours_since(published) if published else 96.0
                        # Even zero-keyword competitor videos are signals
                        opportunities.append(Opportunity(
                            topic=_clean_topic(title),
                            source=f"youtube_rss/{friendly_name}",
                            recency_hours=recency_h,
                            keyword_match=kw,
                            url=link,
                            raw_title=title,
                        ))
                except Exception as exc:
                    log.debug("[youtube_rss] %s error: %s", friendly_name, exc)

        log.info("[youtube_rss] %d competitor videos", len(opportunities))
        return opportunities

    # ──────────────────────────────────────────────────────────────────────────
    # SOURCE 6: SerpAPI — YouTube search + Google Trends
    # Free tier: 250 searches/month
    # ──────────────────────────────────────────────────────────────────────────

    async def _fetch_serpapi_youtube(self) -> list[Opportunity]:
        if not self.serpapi_key:
            return []

        opportunities = []
        SERPAPI_BASE = "https://serpapi.com/search.json"

        async with aiohttp.ClientSession() as session:
            for seed in DARK_SEEDS_PT[:3]:  # conserve free quota
                params = {
                    "engine": "youtube",
                    "search_query": seed,
                    "api_key": self.serpapi_key,
                    "gl": "br",
                    "hl": "pt",
                }
                try:
                    async with session.get(
                        SERPAPI_BASE,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                    for vid in data.get("video_results", [])[:10]:
                        title = vid.get("title", "")
                        link = vid.get("link", "")
                        views_raw = vid.get("views", "0").replace(",", "").replace(".", "")
                        try:
                            views = int("".join(c for c in views_raw if c.isdigit()))
                        except Exception:
                            views = 0
                        kw = _count_dark_keywords(title)
                        opportunities.append(Opportunity(
                            topic=_clean_topic(title),
                            source="serpapi_youtube",
                            engagement_signal=views,
                            recency_hours=72.0,
                            keyword_match=kw,
                            url=link,
                            raw_title=title,
                        ))
                    await asyncio.sleep(0.5)
                except Exception as exc:
                    log.debug("[serpapi] seed '%s' error: %s", seed, exc)

        log.info("[serpapi] %d videos", len(opportunities))
        return opportunities

    # ──────────────────────────────────────────────────────────────────────────
    # Deduplication
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _deduplicate(items: list[Opportunity]) -> list[Opportunity]:
        """Merge near-duplicate topics using simple token overlap."""
        seen: dict[str, Opportunity] = {}
        for item in items:
            key = _normalize_key(item.topic)
            if key not in seen:
                seen[key] = item
            else:
                # Keep the one with higher engagement or keyword score
                existing = seen[key]
                if (item.engagement_signal + item.keyword_match * 100) > (
                    existing.engagement_signal + existing.keyword_match * 100
                ):
                    seen[key] = item
        return list(seen.values())


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

# Extended dark keyword list (Portuguese + English)
_DARK_KEYWORDS = {
    # Portuguese crime/dark
    "crime", "assassinato", "assassino", "serial killer", "killer",
    "morte", "morto", "morta", "cadáver", "cadaver", "óbito",
    "misterio", "mistério", "mysterio", "caso", "policia", "polícia",
    "psicopata", "sociopata", "perturbador", "perturbadora",
    "macabro", "macabra", "horror", "terror", "horrivel", "horrível",
    "tragédia", "tragedia", "sequestro", "estupro", "violência", "violencia",
    "desaparecimento", "desaparecido", "desaparecida",
    "golpe", "fraude", "corrupção", "corrupcao",
    "suicídio", "suicidio", "acidente", "explosão", "explosao",
    "roubo", "assalto", "bandido", "criminoso",
    "chocante", "perturbador", "bizarro", "sombrio",
    "escondido", "segredo", "oculto", "verdade oculta",
    "investigação", "investigacao", "denúncia", "denuncia",
    # English (for RSS/Reddit EN posts)
    "murder", "killed", "victim", "criminal", "conspiracy",
    "unsolved", "mystery", "dark", "shocking", "disturbing",
    "trafficking", "abuse", "scandal", "fraud", "death",
}


def _count_dark_keywords(text: str) -> int:
    """Count how many dark keywords appear in text (case-insensitive)."""
    text_lower = text.lower()
    return sum(1 for kw in _DARK_KEYWORDS if kw in text_lower)


def _hours_since(timestamp_str: str) -> float:
    """Return hours since a timestamp string. Returns 168 (1 week) on parse failure."""
    if not timestamp_str:
        return 168.0
    from email.utils import parsedate_to_datetime
    try:
        # ISO 8601 (YouTube API)
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        pass
    try:
        # RFC 2822 (RSS / feedparser)
        dt = parsedate_to_datetime(timestamp_str)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except Exception:
        return 168.0


def _clean_topic(raw: str) -> str:
    """Strip noise and truncate for use as a pipeline topic string."""
    import re
    # Remove source site suffixes like " - G1", " | Folha", etc.
    cleaned = re.sub(r"\s*[\|\-–]\s*\w[\w\s]{0,25}$", "", raw).strip()
    # Remove leading/trailing quotes
    cleaned = cleaned.strip('"\'«»')
    return cleaned[:120]


def _normalize_key(topic: str) -> str:
    """Lowercase, strip punctuation, collapse spaces — used for dedup."""
    import re
    t = topic.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # Keep only first 60 chars for fuzzy match
    return t[:60]


# Late import to avoid circular dependency
from .scorer import OpportunityScorer  # noqa: E402
