"""
NotebookLMBridge — integrates Google NotebookLM with the CineForge trend pipeline.

Two integration paths:
  A) notebooklm-mcp package (pip install notebooklm-mcp)
     Connects over MCP (Model Context Protocol) — the recommended path.
     Requires Google account authentication (browser-based OAuth once).

  B) Gemini API fallback (no extra package needed)
     Uses the existing GEMINI_API_KEY from settings to do the same research
     via Gemini 2.0 Flash with grounding enabled.

Usage:
    bridge = NotebookLMBridge()
    refined = bridge.research_opportunity("serial killer no Brasil nos anos 90")
    # refined is an EnrichedResearch object with title suggestions,
    # content outline, and target audience notes.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


@dataclass
class EnrichedResearch:
    """Structured output from NotebookLM / Gemini deep research."""
    original_topic: str
    refined_topic: str
    # 5 YouTube title variants (curiosity hooks)
    title_variants: list[str] = field(default_factory=list)
    # Brief outline of 6-8 key narrative points
    narrative_outline: list[str] = field(default_factory=list)
    # Recommended tags for YouTube upload
    youtube_tags: list[str] = field(default_factory=list)
    # Thumbnail concept description
    thumbnail_concept: str = ""
    # Sources / references found
    sources: list[str] = field(default_factory=list)
    # Raw research text
    raw_notes: str = ""
    confidence: float = 0.0   # 0-1 estimate of research quality


class NotebookLMBridge:
    """
    Connects NotebookLM (via MCP) or Gemini (fallback) to enrich
    raw TrendMonitor opportunities with deep research notes.
    """

    def __init__(
        self,
        gemini_api_key: str | None = None,
        notebooklm_notebook_id: str | None = None,
        use_notebooklm_mcp: bool = True,
    ):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY", "")
        # NotebookLM notebook to add sources to and query
        self.notebook_id = notebooklm_notebook_id or os.getenv("NOTEBOOKLM_NOTEBOOK_ID", "")
        self.use_notebooklm_mcp = use_notebooklm_mcp
        self._mcp_client = None

        if use_notebooklm_mcp:
            self._mcp_client = self._init_mcp()

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def research_opportunity(self, topic: str) -> EnrichedResearch:
        """
        Run deep research on a topic via NotebookLM MCP (or Gemini fallback).
        Returns EnrichedResearch with title variants, outline, and tags.
        """
        if self._mcp_client:
            try:
                return self._research_via_notebooklm(topic)
            except Exception as exc:
                log.warning("[NotebookLMBridge] MCP failed (%s) — falling back to Gemini.", exc)

        if self.gemini_api_key:
            return self._research_via_gemini(topic)

        log.error("[NotebookLMBridge] No research backend available. Set GEMINI_API_KEY.")
        return EnrichedResearch(original_topic=topic, refined_topic=topic)

    def add_sources_to_notebook(self, urls: list[str]) -> bool:
        """
        Add external URLs as sources to the active NotebookLM notebook.
        Enables Deep Research mode to ingest them automatically.
        Returns True on success.
        """
        if not self._mcp_client:
            log.warning("[NotebookLMBridge] MCP not available — cannot add sources.")
            return False
        try:
            for url in urls:
                self._mcp_client.add_source(
                    notebook_id=self.notebook_id,
                    source_type="url",
                    content=url,
                )
                log.info("[NotebookLMBridge] Added source: %s", url)
            return True
        except Exception as exc:
            log.warning("[NotebookLMBridge] add_sources error: %s", exc)
            return False

    # ──────────────────────────────────────────────────────────────────────────
    # Path A: NotebookLM via MCP
    # Install: pip install notebooklm-mcp
    # Docs: https://github.com/khengyun/notebooklm-mcp
    # ──────────────────────────────────────────────────────────────────────────

    def _init_mcp(self):
        """Try to import and initialise the notebooklm-mcp client."""
        try:
            from notebooklm_mcp import NotebookLMClient  # type: ignore
            client = NotebookLMClient()
            log.info("[NotebookLMBridge] notebooklm-mcp client initialised.")
            return client
        except ImportError:
            log.info(
                "[NotebookLMBridge] notebooklm-mcp not installed "
                "(pip install notebooklm-mcp). Using Gemini fallback."
            )
            return None
        except Exception as exc:
            log.warning("[NotebookLMBridge] MCP init error: %s", exc)
            return None

    def _research_via_notebooklm(self, topic: str) -> EnrichedResearch:
        """
        Query NotebookLM Deep Research mode for the topic.
        NotebookLM Deep Research (Nov 2025) actively searches the web.
        """
        prompt = _build_research_prompt(topic)

        # Create or reuse notebook
        nb_id = self.notebook_id
        if not nb_id:
            nb = self._mcp_client.create_notebook(title=f"CineForge Research: {topic[:50]}")
            nb_id = nb.get("id", "")

        # Deep Research query
        result = self._mcp_client.query(
            notebook_id=nb_id,
            query=prompt,
            mode="deep_research",     # activates agentic search
        )

        raw = result.get("response", "")
        return _parse_research_response(topic, raw)

    # ──────────────────────────────────────────────────────────────────────────
    # Path B: Gemini API with grounding (web search via Google)
    # Docs: https://ai.google.dev/gemini-api/docs/grounding
    # ──────────────────────────────────────────────────────────────────────────

    def _research_via_gemini(self, topic: str) -> EnrichedResearch:
        """
        Use Gemini 2.0 Flash with Google Search grounding for deep research.
        Grounding is available in the free tier of Google AI Studio.
        """
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            log.error("[NotebookLMBridge] google-generativeai not installed.")
            return EnrichedResearch(original_topic=topic, refined_topic=topic)

        genai.configure(api_key=self.gemini_api_key)

        # Gemini 2.0 Flash with Google Search tool (grounding)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            tools=["google_search_retrieval"],   # enables web grounding
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
                response_mime_type="application/json",
            ),
        )

        prompt = _build_research_prompt(topic)

        try:
            response = model.generate_content(prompt)
            raw = response.text.strip()
            # Strip code fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()
            return _parse_research_response(topic, raw)
        except Exception as exc:
            log.warning("[NotebookLMBridge] Gemini research error: %s", exc)
            # Return minimal enrichment from topic string alone
            return EnrichedResearch(
                original_topic=topic,
                refined_topic=topic,
                title_variants=[topic],
                confidence=0.1,
            )


# ──────────────────────────────────────────────────────────────────────────────
# Prompt + response parser
# ──────────────────────────────────────────────────────────────────────────────

def _build_research_prompt(topic: str) -> str:
    return f"""
Você é um pesquisador especialista em conteúdo dark/crime para YouTube em Português Brasileiro.

Pesquise profundamente o seguinte tópico e retorne um JSON com EXATAMENTE esta estrutura:
{{
  "refined_topic": "<versão melhorada do tópico para YouTube>",
  "title_variants": ["<título 1>", "<título 2>", "<título 3>", "<título 4>", "<título 5>"],
  "narrative_outline": [
    "<ponto narrativo 1>",
    "<ponto narrativo 2>",
    "<ponto narrativo 3>",
    "<ponto narrativo 4>",
    "<ponto narrativo 5>",
    "<ponto narrativo 6>"
  ],
  "youtube_tags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>",
                   "<tag6>", "<tag7>", "<tag8>", "<tag9>", "<tag10>"],
  "thumbnail_concept": "<descrição visual da miniatura ideal para YouTube>",
  "sources": ["<url ou referência 1>", "<url ou referência 2>"],
  "confidence": 0.0
}}

REGRAS:
- Títulos: devem ser CHOCANTES, com gancho emocional, entre 60-70 caracteres
- Narrative outline: fatos reais e verificáveis, ordenados dramaticamente
- Tags: mix de termos de busca populares + específicos do caso
- Thumbnail: descreva cores, texto, imagens — deve gerar curiosidade extrema
- Confidence: 0.0-1.0 baseado na quantidade de informação real encontrada

TÓPICO: {topic}
""".strip()


def _parse_research_response(topic: str, raw: str) -> EnrichedResearch:
    """Parse JSON response into EnrichedResearch; handle partial/malformed JSON."""
    try:
        data = json.loads(raw)
        return EnrichedResearch(
            original_topic=topic,
            refined_topic=data.get("refined_topic", topic),
            title_variants=data.get("title_variants", [topic]),
            narrative_outline=data.get("narrative_outline", []),
            youtube_tags=data.get("youtube_tags", []),
            thumbnail_concept=data.get("thumbnail_concept", ""),
            sources=data.get("sources", []),
            raw_notes=raw,
            confidence=float(data.get("confidence", 0.5)),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        log.warning("[NotebookLMBridge] JSON parse error (%s) — raw: %s…", exc, raw[:120])
        return EnrichedResearch(
            original_topic=topic,
            refined_topic=topic,
            raw_notes=raw,
            confidence=0.2,
        )
