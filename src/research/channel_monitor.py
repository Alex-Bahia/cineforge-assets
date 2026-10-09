"""
channel_monitor.py — Competitor RSS-feed monitor + viral-content detector.

Architecture
------------
1. RSSSubscriber    — subscribes to competitor YouTube channel RSS feeds
                       (feedparser, zero-auth, returns last 15 uploads per channel)
2. VideoEnricher    — attaches view/like counts via YouTube Data API v3 (optional)
3. ViralDetector    — scores each video 0–10 using velocity + engagement + title hooks
4. PatternExtractor — extracts keyword/topic patterns from viral videos
5. OpportunityScorer— ranks topics as ContentOpportunity objects (multi-factor score)
6. NotebookLM/Gemini integration — enriches top opportunities with deep research

Pre-loaded catalogue: 12 top Brazilian dark / true-crime YouTube channels (Oct 2025).
Access via  ChannelMonitor.DARK_BR_CHANNELS.

Run standalone
--------------
    python -m src.research.channel_monitor

From code
---------
    from src.research.channel_monitor import ChannelMonitor
    monitor = ChannelMonitor()
    report  = monitor.scan()          # blocking — runs full pipeline
    opps    = monitor.get_opportunities()   # ranked list from last scan

Environment variables (from .env / config/settings.py)
-------------------------------------------------------
    YOUTUBE_DATA_API_KEY   — optional; enables real view-count fetching
    GEMINI_API_KEY         — optional; enables Gemini title/thumbnail generation
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import math
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Brazilian Dark / True-Crime Channel Catalogue
# ---------------------------------------------------------------------------
# Channel IDs verified via YouTube RSS endpoint (Oct 2025).
# Format: https://www.youtube.com/feeds/videos.xml?channel_id=<channel_id>

DARK_BR_CHANNELS: list[dict] = [
    {
        "name": "ICrim",
        "channel_id": "UCqBsh7pAMHTzVFVDxKs_8lg",
        "category": "true_crime",
        "avg_views": 2_000_000,
        "description": "True crime e casos policiais brasileiros — maior canal do gênero no BR",
    },
    {
        "name": "Boletim do Crime",
        "channel_id": "UC3BmKKUQRKu8oTVdAEoiM3A",
        "category": "true_crime",
        "avg_views": 1_200_000,
        "description": "Boletins policiais detalhados e casos criminais reais",
    },
    {
        "name": "Holder Canal",
        "channel_id": "UCBcsGRbWz8bAh-okyKL7C4A",
        "category": "dark_mystery",
        "avg_views": 3_500_000,
        "description": "Mistério, dark web, casos investigativos — canal principal dark BR",
    },
    {
        "name": "Kadê Herman",
        "channel_id": "UCWNQVLzLCWHMt0Wz9qAUowA",
        "category": "dark_mystery",
        "avg_views": 900_000,
        "description": "Investigações, dark web, conspirações e paranormal",
    },
    {
        "name": "Terror e Mistério Brasil",
        "channel_id": "UCJqrNkyOiC5OkGmh-6hMbMg",
        "category": "horror_mystery",
        "avg_views": 600_000,
        "description": "Terror, horror, lendas urbanas e mistérios brasileiros",
    },
    {
        "name": "Crime Sem Fronteiras",
        "channel_id": "UC2mRhJGiNhxbHzTKrGM5CGA",
        "category": "true_crime",
        "avg_views": 700_000,
        "description": "Crimes internacionais e nacionais com análise aprofundada",
    },
    {
        "name": "Mundo Criminal",
        "channel_id": "UCLcf3VuHqbYoQW-5pn85_vg",
        "category": "true_crime",
        "avg_views": 500_000,
        "description": "Documentários sobre o submundo criminal e facções",
    },
    {
        "name": "Estudo do Crime",
        "channel_id": "UCYshfgBrjBOQarS-8bzmhyg",
        "category": "true_crime",
        "avg_views": 400_000,
        "description": "Análise criminológica, perfil de serial killers, casos reais",
    },
    {
        "name": "Planeta Bizarro",
        "channel_id": "UCNd24w2WMiPdD9FXJTIOmJw",
        "category": "dark_mystery",
        "avg_views": 1_100_000,
        "description": "Casos bizarros, mistérios e fenômenos inexplicáveis",
    },
    {
        "name": "Além do Horizonte",
        "channel_id": "UCvzYk3rJWDhpuKxVOPx5ULA",
        "category": "conspiracy",
        "avg_views": 550_000,
        "description": "Conspirações, teorias e mistérios globais",
    },
    {
        "name": "Curiosidades Macabras",
        "channel_id": "UCFXJjMz_kBCOcBi3OP4Dz3Q",
        "category": "dark_mystery",
        "avg_views": 450_000,
        "description": "Curiosidades macabras, casos sombrios e histórias perturbadoras",
    },
    {
        "name": "Serial Killer Brasil",
        "channel_id": "UCxzSUFw8bEhWBjr29HpIRNA",
        "category": "true_crime",
        "avg_views": 800_000,
        "description": "Serial killers brasileiros — histórias completas e documentadas",
    },
]

# YouTube feed / URL templates
YT_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
YT_VIDEO_URL    = "https://www.youtube.com/watch?v={video_id}"
YT_CHANNEL_URL  = "https://www.youtube.com/channel/{channel_id}"


# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class ChannelVideo:
    """One video entry from a channel RSS feed (optionally enriched via API)."""
    video_id: str
    title: str
    channel_id: str
    channel_name: str
    published: datetime
    description: str = ""
    thumbnail_url: str = ""
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    duration_seconds: int = 0
    tags: list[str] = field(default_factory=list)
    # Computed by ViralDetector
    viral_score: float = 0.0
    hours_since_published: float = 0.0
    views_per_hour: float = 0.0
    is_new: bool = False               # True if not seen in previous scan
    fetched_at: str = ""


@dataclass
class ContentOpportunity:
    """A ranked content-topic opportunity derived from competitor analysis."""
    topic: str
    channel_source: str
    category: str = "dark"
    viral_score: float = 0.0
    opportunity_score: float = 0.0    # 0–10 composite
    competition: str = "medium"        # low / medium / high
    estimated_views: int = 0
    key_keywords: list[str] = field(default_factory=list)
    title_hooks: list[str] = field(default_factory=list)
    thumbnail_concept: str = ""
    evidence_videos: list[str] = field(default_factory=list)  # video IDs
    notebooklm_notes: str = ""
    discovered_at: str = ""


# ---------------------------------------------------------------------------
# RSSSubscriber
# ---------------------------------------------------------------------------

class RSSSubscriber:
    """
    Subscribes to YouTube channel RSS feeds using feedparser (zero-auth).
    YouTube RSS returns the last 15 uploaded videos per channel.

    Feed URL: https://www.youtube.com/feeds/videos.xml?channel_id=<id>
    """

    def __init__(self, channels: list[dict] | None = None) -> None:
        self._channels = channels or DARK_BR_CHANNELS
        self._session = requests.Session()
        self._session.headers["User-Agent"] = (
            "Mozilla/5.0 (X11; Linux x86_64) CineForge/2.0"
        )

    def fetch_channel(
        self,
        channel: dict,
        newer_than_hours: int = 168,
    ) -> list[ChannelVideo]:
        """
        Fetch videos from a single channel RSS feed.
        Only returns videos published in the last `newer_than_hours` window.
        """
        try:
            import feedparser  # type: ignore[import]
        except ImportError:
            log.error("feedparser not installed — run: pip install feedparser>=6.0.10")
            return []

        channel_id   = channel["channel_id"]
        channel_name = channel["name"]
        url          = YT_RSS_TEMPLATE.format(channel_id=channel_id)

        try:
            feed = feedparser.parse(url)
        except Exception as exc:
            log.warning("[RSS] feedparser error for %s: %s", channel_name, exc)
            return []

        if getattr(feed, "bozo", False) and not feed.entries:
            log.warning("[RSS] Bad feed for %s (bozo=%s)", channel_name,
                        getattr(feed, "bozo_exception", "?"))
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=newer_than_hours)
        now    = datetime.now(timezone.utc)
        videos: list[ChannelVideo] = []

        for entry in feed.entries:
            # ── Publish date ────────────────────────────────────────────
            try:
                pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pub = now

            if pub < cutoff:
                continue

            # ── Video ID ────────────────────────────────────────────────
            video_id = ""
            link = entry.get("link", "")
            m = re.search(r"v=([A-Za-z0-9_\-]{11})", link)
            if m:
                video_id = m.group(1)
            if not video_id:
                # Try yt:videoId tag
                video_id = entry.get("yt_videoid", "")

            # ── Thumbnail ───────────────────────────────────────────────
            thumbnail_url = ""
            media_thumbs = entry.get("media_thumbnail", [])
            if media_thumbs:
                thumbnail_url = media_thumbs[0].get("url", "")

            hours_since = max((now - pub).total_seconds() / 3600, 0.1)

            video = ChannelVideo(
                video_id=video_id,
                title=entry.get("title", ""),
                channel_id=channel_id,
                channel_name=channel_name,
                published=pub,
                description=entry.get("summary", "")[:500],
                thumbnail_url=thumbnail_url,
                hours_since_published=hours_since,
                is_new=(hours_since <= 72),
                fetched_at=now.isoformat(),
            )
            videos.append(video)

        log.info("[RSS] %-30s  %2d videos (window: %dh)",
                 channel_name, len(videos), newer_than_hours)
        return videos

    def fetch_all(self, newer_than_hours: int = 168) -> list[ChannelVideo]:
        """Fetch videos from all subscribed channels (sequential + polite delay)."""
        all_videos: list[ChannelVideo] = []
        for ch in self._channels:
            vids = self.fetch_channel(ch, newer_than_hours)
            all_videos.extend(vids)
            time.sleep(0.3)  # polite rate-limiting
        log.info("[RSS] Total fetched: %d videos from %d channels",
                 len(all_videos), len(self._channels))
        return all_videos

    async def fetch_all_async(self, newer_than_hours: int = 168) -> list[ChannelVideo]:
        """Non-blocking version — runs fetch_all in an executor thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.fetch_all, newer_than_hours)


# ---------------------------------------------------------------------------
# VideoEnricher — YouTube Data API v3
# ---------------------------------------------------------------------------

class VideoEnricher:
    """
    Fetches view/like/comment counts and duration for video IDs via YouTube Data API v3.
    Batch-requests up to 50 IDs per call (1 quota unit each).
    Gracefully skips enrichment when no API key is provided.
    """

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key or os.getenv("YOUTUBE_DATA_API_KEY", "")

    def enrich_batch(self, videos: list[ChannelVideo]) -> list[ChannelVideo]:
        """Attach real statistics to each ChannelVideo in-place."""
        if not self._api_key:
            log.debug("[Enricher] No YouTube API key — skipping stat enrichment.")
            return videos

        video_map = {v.video_id: v for v in videos if v.video_id}
        ids       = list(video_map.keys())
        # Chunks of 50 (API maximum)
        for chunk in [ids[i:i + 50] for i in range(0, len(ids), 50)]:
            self._fetch_stats(chunk, video_map)
            time.sleep(0.5)

        return videos

    def _fetch_stats(self, ids: list[str], video_map: dict[str, ChannelVideo]) -> None:
        url    = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(ids),
            "key": self._api_key,
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            for item in resp.json().get("items", []):
                vid_id  = item.get("id", "")
                stats   = item.get("statistics", {})
                content = item.get("contentDetails", {})
                if vid_id not in video_map:
                    continue
                v = video_map[vid_id]
                v.view_count    = int(stats.get("viewCount",    0))
                v.like_count    = int(stats.get("likeCount",    0))
                v.comment_count = int(stats.get("commentCount", 0))
                v.duration_seconds = _parse_iso_duration(content.get("duration", "PT0S"))
        except Exception as exc:
            log.warning("[Enricher] Stats fetch failed (chunk size %d): %s", len(ids), exc)


def _parse_iso_duration(iso: str) -> int:
    """Convert ISO 8601 duration string (PT8M22S) to total seconds."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m:
        return 0
    return int(m.group(1) or 0) * 3600 + int(m.group(2) or 0) * 60 + int(m.group(3) or 0)


# ---------------------------------------------------------------------------
# ViralDetector
# ---------------------------------------------------------------------------

class ViralDetector:
    """
    Scores each video 0–10 on a viral potential scale.

    Score components
    ----------------
    velocity  (0–4 pts) — views per hour (log-scaled)
    engagement(0–3 pts) — like-rate + comment-rate
    title_hook(0–2 pts) — presence of emotionally charged keywords
    recency   (0–1 pt)  — < 24 h = 1, < 72 h = 0.5, older = 0
    """

    # PT keywords that signal high CTR / viral potential in dark content
    VIRAL_KEYWORDS: list[str] = [
        "chocante", "inacreditável", "perturbador", "bizarro", "macabro",
        "monstruoso", "horrível", "assustador", "revoltante", "impactante",
        "verdade", "revelado", "descoberto", "proibido", "secreto",
        "dark web", "serial killer", "assassino", "crime", "morte",
        "desaparecimento", "sequestro", "tortura", "massacr", "psicopata",
        "detalhes", "história real", "caso real", "nunca contado",
        "finalmente", "policial", "preso", "monstruosidade", "misterioso",
        "investigação", "suspeito", "culpado", "cometeu", "confessou",
    ]

    def score_video(self, video: ChannelVideo) -> ChannelVideo:
        """Compute viral_score and views_per_hour for a single video in-place."""
        hours  = max(video.hours_since_published, 0.1)
        views  = video.view_count or 0
        vph    = views / hours
        video.views_per_hour = vph

        # ── Velocity (0–4) ──────────────────────────────────────────────
        vel = min(4.0, math.log10(max(vph, 1)) * 1.5) if vph >= 1 else 0.0

        # ── Engagement (0–3) ────────────────────────────────────────────
        eng = 0.0
        if views > 0:
            eng = min(3.0,
                      (video.like_count / views) * 100 * 0.3
                      + (video.comment_count / views) * 100 * 1.5)

        # ── Title hook (0–2) ────────────────────────────────────────────
        title_lc = video.title.lower()
        kw_hits  = sum(1 for kw in self.VIRAL_KEYWORDS if kw in title_lc)
        hook     = min(2.0, kw_hits * 0.4)

        # ── Recency bonus (0–1) ─────────────────────────────────────────
        if hours <= 24:
            rec = 1.0
        elif hours <= 72:
            rec = 0.5
        else:
            rec = 0.0

        video.viral_score = round(vel + eng + hook + rec, 2)
        return video

    def score_batch(self, videos: list[ChannelVideo]) -> list[ChannelVideo]:
        return [self.score_video(v) for v in videos]

    def get_viral(
        self,
        videos: list[ChannelVideo],
        threshold: float = 4.0,
    ) -> list[ChannelVideo]:
        """Return videos above threshold, sorted descending."""
        return sorted(
            [v for v in videos if v.viral_score >= threshold],
            key=lambda v: v.viral_score,
            reverse=True,
        )


# ---------------------------------------------------------------------------
# PatternExtractor
# ---------------------------------------------------------------------------

class PatternExtractor:
    """
    Lightweight NLP-free keyword and topic extraction from video titles.
    Uses TF-IDF-style frequency + bigram clustering.
    """

    _STOP_PT: frozenset[str] = frozenset({
        "de", "da", "do", "dos", "das", "em", "no", "na", "com", "por",
        "para", "que", "uma", "um", "ou", "e", "a", "o", "os", "as",
        "se", "foi", "era", "como", "mais", "mas", "já", "não", "são",
        "ele", "ela", "isso", "isto", "aqui", "ao", "à", "depois", "antes",
        "eu", "você", "nós", "eles", "elas", "sua", "seu", "seus", "suas",
        "esse", "essa", "este", "esta", "ter", "ser", "está", "muito",
    })

    def _words(self, text: str) -> list[str]:
        return [
            w for w in re.findall(r"\b[a-zA-ZÀ-ú]{4,}\b", text.lower())
            if w not in self._STOP_PT
        ]

    def extract_keywords(
        self,
        videos: list[ChannelVideo],
        top_n: int = 30,
    ) -> list[tuple[str, int]]:
        """Return (keyword, count) tuples sorted by frequency."""
        counts: Counter = Counter()
        for v in videos:
            for w in self._words(v.title):
                counts[w] += 1
        return counts.most_common(top_n)

    def extract_topics(self, videos: list[ChannelVideo]) -> list[str]:
        """
        Build topic clusters from bigrams that appear 2+ times across titles.
        """
        bigrams: Counter = Counter()
        for v in videos:
            ws = self._words(v.title)
            for i in range(len(ws) - 1):
                bigrams[f"{ws[i]} {ws[i+1]}"] += 1
        return [bg for bg, cnt in bigrams.most_common(20) if cnt >= 2]

    def channel_signature(
        self,
        channel_name: str,
        videos: list[ChannelVideo],
    ) -> dict:
        """Channel-level stats: dominant keywords, avg views, posting cadence."""
        ch = [v for v in videos if v.channel_name == channel_name]
        if not ch:
            return {}
        avg_v  = int(sum(v.view_count for v in ch) / len(ch))
        max_v  = max(v.view_count for v in ch)
        kws    = [kw for kw, _ in self.extract_keywords(ch, 8)]
        cadence = 168.0
        if len(ch) >= 2:
            dates   = sorted(v.published for v in ch)
            spans   = [(dates[i+1] - dates[i]).total_seconds() / 3600 for i in range(len(dates) - 1)]
            cadence = round(sum(spans) / len(spans), 1)
        return {
            "channel": channel_name,
            "video_count": len(ch),
            "avg_views": avg_v,
            "max_views": max_v,
            "avg_cadence_hours": cadence,
            "top_keywords": kws,
        }


# ---------------------------------------------------------------------------
# OpportunityScorer
# ---------------------------------------------------------------------------

class OpportunityScorer:
    """
    Converts viral videos + keyword patterns into ranked ContentOpportunity objects.

    Scoring formula
    ---------------
    opportunity_score =
        0.40 * viral_score        (raw viral signal from ViralDetector)
      + 0.30 * (10 - 10*comp)    (lower competition = higher score)
      + 0.20 * (10 * recency)    (newer = more relevant)
      + 0.10 * (10 * authority)  (high-authority channel as source = confirmed niche)
    """

    def __init__(self, gemini_api_key: str = "") -> None:
        self._api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")

    def score_opportunities(
        self,
        viral_videos: list[ChannelVideo],
        all_videos: list[ChannelVideo],
        extractor: PatternExtractor,
    ) -> list[ContentOpportunity]:
        """Build and rank ContentOpportunity objects from viral videos."""
        if not viral_videos:
            return []

        keywords = extractor.extract_keywords(viral_videos, top_n=15)

        # Bucket videos by their dominant keyword
        groups: dict[str, list[ChannelVideo]] = defaultdict(list)
        for video in viral_videos:
            assigned = False
            for kw, _ in keywords:
                if kw in video.title.lower():
                    groups[kw].append(video)
                    assigned = True
                    break
            if not assigned:
                groups["outros"].append(video)

        opportunities: list[ContentOpportunity] = []
        for topic, group in groups.items():
            if not group:
                continue
            best = max(group, key=lambda v: v.viral_score)

            # Competition: how many distinct channels cover this topic
            n_channels       = len({v.channel_id for v in group})
            comp_factor      = min(1.0, n_channels / 5)
            competition      = ("low" if n_channels <= 1
                                else "medium" if n_channels <= 3
                                else "high")

            # Recency
            avg_age_h    = sum(v.hours_since_published for v in group) / len(group)
            rec_factor   = max(0.0, 1.0 - avg_age_h / 168)

            # Channel authority
            ch_meta      = next((c for c in DARK_BR_CHANNELS
                                 if c["name"] == best.channel_name), {})
            auth_factor  = min(1.0, ch_meta.get("avg_views", 500_000) / 3_000_000)

            opp_score = (
                0.40 * best.viral_score
                + 0.30 * (10 * (1 - comp_factor))
                + 0.20 * (10 * rec_factor)
                + 0.10 * (10 * auth_factor)
            )

            opp = ContentOpportunity(
                topic=topic,
                channel_source=best.channel_name,
                category=ch_meta.get("category", "dark"),
                viral_score=best.viral_score,
                opportunity_score=round(opp_score, 2),
                competition=competition,
                estimated_views=int(best.views_per_hour * 72),
                key_keywords=[kw for kw, _ in extractor.extract_keywords(group, 5)],
                evidence_videos=[v.video_id for v in group[:3]],
                discovered_at=datetime.now(timezone.utc).isoformat(),
            )
            opportunities.append(opp)

        opportunities.sort(key=lambda o: o.opportunity_score, reverse=True)
        log.info("[Scorer] %d opportunities ranked", len(opportunities))
        return opportunities

    def enrich_with_gemini(
        self,
        opp: ContentOpportunity,
        notebook: object | None = None,
    ) -> ContentOpportunity:
        """
        Use GeminiNotebook (grounded search) to generate title hooks +
        thumbnail concept for a ContentOpportunity.
        Mutates the object in-place and also returns it.
        """
        if not self._api_key:
            return opp

        # Lazy import to avoid circular-dependency at module load time
        from src.research.gemini_notebook import GeminiNotebook  # type: ignore[import]

        nb = notebook or GeminiNotebook(
            title=f"CineForge — {opp.topic}",
            gemini_api_key=self._api_key,
            use_grounding=True,
        )

        question = (
            f"Crie 5 títulos virais para YouTube sobre o tópico: '{opp.topic}'. "
            f"O canal é de conteúdo dark/true-crime em Português Brasileiro. "
            f"Inclua também um conceito de thumbnail impactante. "
            f"Responda SOMENTE em JSON com as chaves 'titles' (lista de strings) "
            f"e 'thumbnail' (string com descrição visual)."
        )
        result = nb.query(question)

        try:
            raw = result.answer.strip()
            # Strip markdown code fences if present
            fence_m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            raw = fence_m.group(1).strip() if fence_m else raw
            data = json.loads(raw)
            opp.title_hooks      = data.get("titles", [])
            opp.thumbnail_concept = data.get("thumbnail", "")
        except Exception:
            # Graceful fallback: extract quoted strings as title candidates
            opp.title_hooks = re.findall(r'"([^"]{10,100})"', result.answer)[:5]

        opp.notebooklm_notes = result.answer
        return opp


# ---------------------------------------------------------------------------
# ChannelMonitor  (main orchestrator)
# ---------------------------------------------------------------------------

class ChannelMonitor:
    """
    Full competitor-channel monitoring pipeline.

    Steps
    -----
    1. RSSSubscriber  → fetch last N videos from each configured channel
    2. Mark new vs. previously-seen videos (persists seen IDs to disk)
    3. VideoEnricher  → attach real view/like counts (YouTube Data API)
    4. ViralDetector  → score every video 0–10
    5. PatternExtractor → extract keyword/topic patterns from viral videos
    6. OpportunityScorer → rank topics by opportunity score
    7. GeminiNotebook/NotebookLMBridge → enrich top-3 with deep research
    8. Persist report → research_cache/channel_monitor_report.json
    9. Append to batch/topics.csv for the video pipeline

    Parameters
    ----------
    channels : list[dict] | None
        Channels to monitor (defaults to DARK_BR_CHANNELS).
    youtube_api_key : str
        Optional; enables real view-count enrichment.
    gemini_api_key : str
        Optional; enables AI title/thumbnail generation.
    newer_than_hours : int
        Scan window in hours (default 168 = 7 days).
    viral_threshold : float
        Minimum viral score 0–10 to consider a video viral (default 4.0).
    output_dir : Path | None
        Directory for cache files (default: <project>/research_cache/).
    """

    DARK_BR_CHANNELS = DARK_BR_CHANNELS  # expose as class attribute

    def __init__(
        self,
        channels: list[dict] | None = None,
        youtube_api_key: str = "",
        gemini_api_key: str = "",
        newer_than_hours: int = 168,
        viral_threshold: float = 4.0,
        output_dir: Path | None = None,
    ) -> None:
        self._channels         = channels or DARK_BR_CHANNELS
        self._yt_key           = youtube_api_key or os.getenv("YOUTUBE_DATA_API_KEY", "")
        self._gemini_key       = gemini_api_key  or os.getenv("GEMINI_API_KEY", "")
        self._newer_than_hours = newer_than_hours
        self._viral_threshold  = viral_threshold
        self._output_dir       = output_dir or (
            Path(__file__).parent.parent.parent / "research_cache"
        )
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._rss       = RSSSubscriber(self._channels)
        self._enricher  = VideoEnricher(self._yt_key)
        self._detector  = ViralDetector()
        self._extractor = PatternExtractor()
        self._scorer    = OpportunityScorer(self._gemini_key)

        # Persist seen video IDs across runs so only *new* videos surface
        self._seen_ids: set[str] = self._load_seen_ids()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> dict:
        """
        Execute a full monitoring cycle (blocking).
        Returns a summary dict — also persisted to research_cache/.
        """
        log.info("[ChannelMonitor] Scan starting — %d channels, window=%dh",
                 len(self._channels), self._newer_than_hours)

        # 1. RSS fetch
        all_videos = self._rss.fetch_all(self._newer_than_hours)

        # 2. Tag new videos, persist seen IDs
        new_count = 0
        for v in all_videos:
            if v.video_id and v.video_id not in self._seen_ids:
                v.is_new = True
                self._seen_ids.add(v.video_id)
                new_count += 1
        self._save_seen_ids()
        log.info("[ChannelMonitor] %d new videos (unseen in previous scans)", new_count)

        # 3. Enrich with API stats
        enriched = self._enricher.enrich_batch(all_videos)

        # 4. Score viral potential
        scored = self._detector.score_batch(enriched)
        viral  = self._detector.get_viral(scored, self._viral_threshold)
        log.info("[ChannelMonitor] %d/%d videos above viral threshold %.1f",
                 len(viral), len(scored), self._viral_threshold)

        # 5. Extract patterns from viral (fall back to all scored if too few)
        source_pool = viral if len(viral) >= 5 else scored
        topics   = self._extractor.extract_topics(source_pool)
        keywords = self._extractor.extract_keywords(source_pool, top_n=20)

        # 6. Rank opportunities
        opportunities = self._scorer.score_opportunities(
            source_pool, scored, self._extractor
        )

        # 7. Enrich top-3 with Gemini
        if self._gemini_key:
            for opp in opportunities[:3]:
                try:
                    self._scorer.enrich_with_gemini(opp)
                except Exception as exc:
                    log.warning("[ChannelMonitor] Gemini enrichment failed for '%s': %s",
                                opp.topic, exc)

        # 8. Persist
        report = self._build_report(all_videos, viral, keywords, topics, opportunities)
        self._save_report(report)

        # 9. Append best topics to batch/topics.csv
        self._append_to_csv(opportunities[:10])

        return report

    async def scan_async(self) -> dict:
        """Non-blocking version of scan()."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scan)

    def get_opportunities(self, min_score: float = 5.0) -> list[ContentOpportunity]:
        """Load ContentOpportunity objects from the last persisted scan report."""
        path = self._output_dir / "channel_monitor_report.json"
        if not path.exists():
            log.warning("[ChannelMonitor] No cached report found at %s", path)
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return [
                ContentOpportunity(**o)
                for o in data.get("opportunities", [])
                if o.get("opportunity_score", 0) >= min_score
            ]
        except Exception as exc:
            log.warning("[ChannelMonitor] Could not load report: %s", exc)
            return []

    def add_channel(self, channel: dict) -> None:
        """Dynamically add a channel to monitor at runtime."""
        self._channels.append(channel)
        self._rss = RSSSubscriber(self._channels)
        log.info("[ChannelMonitor] Added channel: %s (%s)",
                 channel.get("name", "?"), channel.get("channel_id", "?"))

    def list_channels(self) -> list[dict]:
        """Return the current channel list."""
        return list(self._channels)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_seen_ids(self) -> set[str]:
        path = self._output_dir / "seen_video_ids.json"
        if path.exists():
            try:
                return set(json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                pass
        return set()

    def _save_seen_ids(self) -> None:
        path = self._output_dir / "seen_video_ids.json"
        try:
            path.write_text(
                json.dumps(sorted(self._seen_ids), ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            log.warning("[ChannelMonitor] Could not persist seen IDs: %s", exc)

    def _build_report(
        self,
        all_videos: list[ChannelVideo],
        viral: list[ChannelVideo],
        keywords: list[tuple[str, int]],
        topics: list[str],
        opportunities: list[ContentOpportunity],
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "generated_at":       now,
            "channels_monitored": len(self._channels),
            "videos_found":       len(all_videos),
            "viral_videos":       len(viral),
            "top_keywords": [
                {"kw": kw, "count": c} for kw, c in keywords
            ],
            "discovered_topics": topics,
            "opportunities": [
                {
                    "topic":            o.topic,
                    "channel_source":   o.channel_source,
                    "category":         o.category,
                    "viral_score":      o.viral_score,
                    "opportunity_score": o.opportunity_score,
                    "competition":      o.competition,
                    "estimated_views":  o.estimated_views,
                    "key_keywords":     o.key_keywords,
                    "title_hooks":      o.title_hooks,
                    "thumbnail_concept": o.thumbnail_concept,
                    "evidence_videos":  o.evidence_videos,
                    "notebooklm_notes": o.notebooklm_notes,
                    "discovered_at":    o.discovered_at,
                }
                for o in opportunities
            ],
            "top_viral_videos": [
                {
                    "video_id":       v.video_id,
                    "title":          v.title,
                    "channel":        v.channel_name,
                    "views":          v.view_count,
                    "views_per_hour": round(v.views_per_hour, 1),
                    "viral_score":    v.viral_score,
                    "hours_old":      round(v.hours_since_published, 1),
                    "is_new":         v.is_new,
                    "url":            YT_VIDEO_URL.format(video_id=v.video_id),
                }
                for v in viral[:20]
            ],
        }

    def _save_report(self, report: dict) -> None:
        path = self._output_dir / "channel_monitor_report.json"
        path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        log.info("[ChannelMonitor] Report saved → %s", path)

    def _append_to_csv(self, opportunities: list[ContentOpportunity]) -> None:
        """Append top opportunity topics to batch/topics.csv for the video pipeline."""
        # Resolve BATCH_CSV from project settings or fallback
        try:
            import sys as _sys
            _sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from config.settings import BATCH_CSV  # type: ignore[import]
            csv_path = Path(BATCH_CSV)
        except Exception:
            csv_path = Path(__file__).parent.parent.parent / "batch" / "topics.csv"

        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing topics to avoid duplicates
        existing: set[str] = set()
        if csv_path.exists():
            try:
                with open(csv_path, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        existing.add(row.get("topic", "").strip().lower())
            except Exception:
                pass

        new_rows = 0
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["topic", "tone", "minutes", "status", "youtube_id"],
            )
            # Header only if file was empty
            if not csv_path.stat().st_size:
                writer.writeheader()

            for opp in opportunities:
                # Prefer first title hook as the topic string
                topic = (opp.title_hooks[0] if opp.title_hooks else opp.topic).strip()
                if not topic or topic.lower() in existing:
                    continue
                writer.writerow({
                    "topic":      topic,
                    "tone":       "suspense e mistério dark",
                    "minutes":    "8",
                    "status":     "",
                    "youtube_id": "",
                })
                existing.add(topic.lower())
                new_rows += 1

        log.info("[ChannelMonitor] %d new topics → %s", new_rows, csv_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


if __name__ == "__main__":
    _setup_logging()

    monitor = ChannelMonitor()
    report  = monitor.scan()

    print("\n" + "=" * 65)
    print(f"  CHANNEL MONITOR  —  {report['generated_at'][:10]}")
    print("=" * 65)
    print(f"  Channels monitored : {report['channels_monitored']}")
    print(f"  Videos fetched     : {report['videos_found']}")
    print(f"  Viral detected     : {report['viral_videos']}")
    print(f"  Opportunities      : {len(report['opportunities'])}")
    print("\n  TOP KEYWORDS:")
    for kw_entry in report["top_keywords"][:12]:
        print(f"    [{kw_entry['count']:>3}x]  {kw_entry['kw']}")
    print("\n  TOP 5 OPPORTUNITIES:")
    for i, opp in enumerate(report["opportunities"][:5], 1):
        print(f"\n  {i}. [{opp['opportunity_score']:.1f}/10]  {opp['topic']}")
        print(f"     Source: {opp['channel_source']}  |  Competition: {opp['competition']}")
        if opp["title_hooks"]:
            print(f"     Best title: {opp['title_hooks'][0]}")
        if opp["key_keywords"]:
            print(f"     Keywords: {', '.join(opp['key_keywords'][:5])}")
    print("\n" + "=" * 65)
