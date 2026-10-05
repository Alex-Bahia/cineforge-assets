"""
gemini_notebook.py — NotebookLM-equivalent RAG pipeline using Gemini API.

Replaces NotebookLM's notebook+source+query model with:
  • Gemini Files API  — upload documents / PDFs / text files as context sources
  • Gemini grounding with Google Search — real-time web knowledge injection
  • google-generativeai (genai) client — same key used by the rest of CineForge

Usage:
    nb = GeminiNotebook(sources=["url1", "url2"], title="My Research")
    result = await nb.query("What are the best dark YouTube channel niches?")
    print(result.answer)
    print(result.citations)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class NotebookSource:
    """One knowledge source inside the notebook."""
    raw: str                          # original URL / file path / plain text
    kind: str = "unknown"             # "url" | "file" | "text" | "youtube"
    content: str = ""                 # fetched/extracted text
    title: str = ""
    bytes_uploaded: int = 0
    gemini_file_uri: str = ""         # filled after Files-API upload


@dataclass
class NotebookResult:
    """Answer returned by GeminiNotebook.query()."""
    answer: str
    citations: list[dict] = field(default_factory=list)
    sources_used: list[str] = field(default_factory=list)
    grounded: bool = False            # True if Google Search grounding was used
    raw_response: str = ""


# ---------------------------------------------------------------------------
# GeminiNotebook
# ---------------------------------------------------------------------------

class GeminiNotebook:
    """
    A notebook that holds multiple knowledge sources and answers questions
    grounded in those sources, optionally augmented with live Google Search.

    Parameters
    ----------
    sources : list[str]
        URLs, local file paths, or raw text strings.
    title : str
        Human-readable name for this research notebook.
    gemini_api_key : str
        Overrides the GEMINI_API_KEY env var / config.settings value.
    model : str
        Gemini model to use.  gemini-2.0-flash-exp has 1M context and is free.
    use_grounding : bool
        If True, augments answers with live Google Search.
    max_sources : int
        Safety cap so we don't blow the context window.
    """

    def __init__(
        self,
        sources: list[str] | None = None,
        title: str = "CineForge Research Notebook",
        gemini_api_key: str = "",
        model: str = "gemini-2.0-flash-exp",
        use_grounding: bool = True,
        max_sources: int = 20,
    ) -> None:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config.settings import GEMINI_API_KEY as cfg_key
        import google.generativeai as genai

        self._genai = genai
        self._api_key = gemini_api_key or cfg_key
        if not self._api_key:
            raise ValueError("GEMINI_API_KEY not set — add it to .env")

        genai.configure(api_key=self._api_key)

        self.title = title
        self.model_name = model
        self.use_grounding = use_grounding
        self.max_sources = max_sources
        self._sources: list[NotebookSource] = []
        self._context_text: str = ""  # final assembled context

        if sources:
            for s in sources[:max_sources]:
                self.add_source(s)

    # ------------------------------------------------------------------
    # Source ingestion
    # ------------------------------------------------------------------

    def add_source(self, raw: str) -> NotebookSource:
        """Add a URL, file path, or plain text as a knowledge source."""
        src = NotebookSource(raw=raw)

        if raw.startswith("http://") or raw.startswith("https://"):
            if "youtube.com" in raw or "youtu.be" in raw:
                src.kind = "youtube"
                src.content = self._fetch_youtube_meta(raw)
                src.title = f"YouTube: {raw}"
            else:
                src.kind = "url"
                src.content, src.title = self._fetch_url(raw)
        elif Path(raw).exists():
            src.kind = "file"
            src.content = Path(raw).read_text(encoding="utf-8", errors="replace")
            src.title = Path(raw).name
        else:
            # treat as raw text
            src.kind = "text"
            src.content = raw
            src.title = raw[:80]

        src.bytes_uploaded = len(src.content.encode())
        self._sources.append(src)
        self._rebuild_context()
        log.info("Added source [%s] %s (%d chars)", src.kind, src.title, src.bytes_uploaded)
        return src

    def _fetch_url(self, url: str, timeout: int = 10) -> tuple[str, str]:
        """Download URL, strip HTML tags, return (text, title)."""
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            html = resp.text

            # Extract <title>
            title_m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
            title = title_m.group(1).strip() if title_m else urlparse(url).netloc

            # Strip tags
            text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:40_000], title   # cap at 40K chars per source
        except Exception as exc:
            log.warning("Could not fetch %s: %s", url, exc)
            return f"[fetch error: {exc}]", url

    def _fetch_youtube_meta(self, url: str) -> str:
        """Use YouTube oEmbed to get title + description without API key."""
        try:
            oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
            data = requests.get(oembed_url, timeout=8).json()
            return f"YouTube video: {data.get('title', 'Unknown')} by {data.get('author_name', 'Unknown')}\nURL: {url}"
        except Exception as exc:
            log.warning("YouTube oEmbed failed for %s: %s", url, exc)
            return f"YouTube: {url}"

    def _rebuild_context(self) -> None:
        """Concatenate all sources into one context string."""
        parts: list[str] = []
        for i, src in enumerate(self._sources, 1):
            parts.append(
                f"=== SOURCE {i}: {src.title} [{src.kind}] ===\n{src.content}\n"
            )
        self._context_text = "\n".join(parts)

    # ------------------------------------------------------------------
    # Query interface
    # ------------------------------------------------------------------

    def query(self, question: str, extra_instruction: str = "") -> NotebookResult:
        """
        Ask a question grounded in the loaded sources + optional live Search.

        Returns a NotebookResult with .answer, .citations and .grounded flag.
        """
        genai = self._genai

        # ── Build generation config ─────────────────────────────────────────
        gen_config = genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=4096,
            response_mime_type="text/plain",
        )

        # ── Grounding tool ──────────────────────────────────────────────────
        tools = []
        if self.use_grounding:
            tools.append(genai.protos.Tool(
                google_search=genai.protos.GoogleSearch()
            ))

        model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=gen_config,
            tools=tools if tools else None,
            system_instruction=(
                "You are an expert research analyst. "
                "Answer questions using the provided source documents as your primary knowledge base. "
                "When sources are insufficient, use your general knowledge and grounded web search. "
                "Always cite your sources with [Source N] references. "
                "Be factual, detailed and structured. Respond in the same language as the question."
            ),
        )

        # ── Compose prompt ──────────────────────────────────────────────────
        context_block = (
            f"## KNOWLEDGE BASE ({len(self._sources)} sources)\n\n{self._context_text}\n\n"
            if self._sources
            else ""
        )

        prompt = (
            f"{context_block}"
            f"## QUESTION\n{question}\n\n"
            f"{extra_instruction}\n"
            "Please provide a comprehensive, structured answer with citations."
        )

        log.info("Querying Gemini notebook: %r (grounding=%s)", question[:80], self.use_grounding)

        try:
            response = model.generate_content(prompt)
            answer_text = response.text

            # Extract citations from grounding metadata if available
            citations: list[dict] = []
            grounded = False
            if hasattr(response, "candidates") and response.candidates:
                cand = response.candidates[0]
                if hasattr(cand, "grounding_metadata") and cand.grounding_metadata:
                    grounded = True
                    meta = cand.grounding_metadata
                    if hasattr(meta, "search_entry_point"):
                        pass  # rendered search widget — not needed here
                    if hasattr(meta, "grounding_chunks"):
                        for chunk in meta.grounding_chunks:
                            if hasattr(chunk, "web"):
                                citations.append({
                                    "title": getattr(chunk.web, "title", ""),
                                    "uri": getattr(chunk.web, "uri", ""),
                                })

            return NotebookResult(
                answer=answer_text,
                citations=citations,
                sources_used=[s.title for s in self._sources],
                grounded=grounded,
                raw_response=str(response),
            )

        except Exception as exc:
            log.error("Gemini query failed: %s", exc)
            return NotebookResult(
                answer=f"[Error querying Gemini: {exc}]",
                grounded=False,
            )

    # ------------------------------------------------------------------
    # Async wrapper (convenience)
    # ------------------------------------------------------------------

    async def aquery(self, question: str, extra_instruction: str = "") -> NotebookResult:
        """Async version — runs query in executor to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.query, question, extra_instruction)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "model": self.model_name,
            "use_grounding": self.use_grounding,
            "sources": [
                {"kind": s.kind, "title": s.title, "raw": s.raw, "bytes": s.bytes_uploaded}
                for s in self._sources
            ],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2))
        log.info("Notebook metadata saved to %s", path)
