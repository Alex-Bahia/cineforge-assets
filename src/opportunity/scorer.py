"""
DarkContentScorer — uses Gemini API to score each opportunity 1-10 for
dark/crime content potential on Brazilian YouTube.

Score meaning:
    1-3   low relevance — generic topic, already over-saturated, or weak hook
    4-6   medium relevance — niche appeal, some untapped angle
    7-8   high relevance — strong emotional hook, verifiable facts, trending now
    9-10  viral potential — shocking, unique, high-engagement likely

The Gemini call returns:
    {
      "ai_score": 8,
      "reasoning": "...",
      "title_variants": ["...", "..."],
      "tags": ["...", "..."],
      "thumbnail_concept": "...",
      "confidence": 0.85
    }

Both Path A (Gemini 2.0 Flash with grounding) and Path B (plain Gemini without
grounding, for quota-constrained environments) are supported.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .database import ScoredOpportunity

log = logging.getLogger(__name__)

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2.0   # seconds between retries


class DarkContentScorer:
    """
    Scores ScoredOpportunity objects using Gemini.

    Usage:
        scorer = DarkContentScorer(api_key="AIza...")
        op = scorer.score(op)   # mutates and returns the same object
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash-exp",
        use_grounding: bool = True,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model
        self.use_grounding = use_grounding
        self._client = None

        if not self.api_key:
            log.warning("[DarkContentScorer] GEMINI_API_KEY not set — scoring disabled.")
        else:
            self._client = self._init_client()

    # ── Public API ────────────────────────────────────────────────────────────

    def score(self, op: "ScoredOpportunity") -> "ScoredOpportunity":
        """
        Compute ai_score (1-10) + final_score for the opportunity.
        Safe to call even without a Gemini key (falls back to heuristic score).
        Returns the same object (mutated in place).
        """
        if not self._client:
            op.ai_score = self._heuristic_score(op)
            op.ai_reasoning = "Heuristic score — Gemini API not configured."
            op.final_score = self._combine_scores(op.raw_score, op.ai_score)
            return op

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = self._call_gemini(op.topic)
                op.ai_score = float(result.get("ai_score", 5))
                op.ai_score = max(1.0, min(10.0, op.ai_score))   # clamp
                op.ai_reasoning = result.get("reasoning", "")
                op.title_variants = result.get("title_variants", [])
                op.tags = list(set(op.tags + result.get("tags", [])))[:20]
                break
            except Exception as exc:
                log.warning(
                    "[DarkContentScorer] Gemini attempt %d/%d failed: %s",
                    attempt, MAX_RETRIES, exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * attempt)
                else:
                    op.ai_score = self._heuristic_score(op)
                    op.ai_reasoning = f"Gemini failed after {MAX_RETRIES} retries; heuristic used."

        op.final_score = self._combine_scores(op.raw_score, op.ai_score)
        return op

    def score_batch(
        self, opportunities: list["ScoredOpportunity"], delay: float = 0.5
    ) -> list["ScoredOpportunity"]:
        """
        Score a list of opportunities sequentially (respects free-tier rate limits).
        Adds a small delay between calls to stay within Gemini free tier (15 RPM).
        """
        scored = []
        for i, op in enumerate(opportunities):
            scored.append(self.score(op))
            if i < len(opportunities) - 1:
                time.sleep(delay)
        return scored

    # ── Gemini client ─────────────────────────────────────────────────────────

    def _init_client(self):
        try:
            import google.generativeai as genai  # type: ignore
            genai.configure(api_key=self.api_key)
            return genai
        except ImportError:
            log.error(
                "[DarkContentScorer] google-generativeai not installed. "
                "Run: pip install google-generativeai"
            )
            return None

    def _call_gemini(self, topic: str) -> dict:
        """
        Send the scoring prompt to Gemini and parse JSON response.
        Uses Google Search grounding when use_grounding=True.
        """
        genai = self._client
        tools = ["google_search_retrieval"] if self.use_grounding else []

        model = genai.GenerativeModel(
            model_name=self.model,
            tools=tools if tools else None,
            generation_config=genai.GenerationConfig(
                temperature=0.4,
                max_output_tokens=1024,
            ),
        )

        prompt = self._build_scoring_prompt(topic)
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        raw = raw.strip()

        return json.loads(raw)

    # ── Prompt ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_scoring_prompt(topic: str) -> str:
        return f"""
Você é um estrategista de conteúdo especializado em canais dark/crime no YouTube Brasil.

Avalie o POTENCIAL VIRAL deste tópico para um canal dark brasileiro e retorne UM JSON com esta estrutura EXATA:
{{
  "ai_score": <inteiro de 1 a 10>,
  "reasoning": "<explicação em 1-2 frases do por quê desta nota>",
  "title_variants": [
    "<Título 1 — chocante, 60-70 chars>",
    "<Título 2 — emocional, 60-70 chars>",
    "<Título 3 — suspense, 60-70 chars>"
  ],
  "tags": ["<tag1>", "<tag2>", "<tag3>", "<tag4>", "<tag5>"],
  "thumbnail_concept": "<descrição de miniatura impactante>",
  "confidence": <float 0.0-1.0>
}}

CRITÉRIOS DE PONTUAÇÃO:
  10 — Caso real, verificável, nunca antes contado em PT-BR, chocante, de alto engajamento
   9 — Caso real bem documentado, ângulo único, forte apelo emocional
   8 — Bom tópico dark, trending agora, moderadamente único
   7 — Relevante para o nicho, informações disponíveis, bom potencial
   6 — Tópico válido mas saturado ou com gancho fraco
   5 — Tópico genérico, pouco diferencial
   1-4 — Irrelevante, muito comum, ou sem potencial dark

TÓPICO: {topic}

Responda SOMENTE com o JSON, sem texto adicional.
""".strip()

    # ── Fallback heuristic ────────────────────────────────────────────────────

    @staticmethod
    def _heuristic_score(op: "ScoredOpportunity") -> float:
        """
        Simple rule-based score 1-10 when Gemini is unavailable.
        Based on: keyword_match, recency, engagement.
        """
        # Map raw_score (0-100) → 1-10
        base = 1.0 + (op.raw_score / 100.0) * 9.0
        # Bonus for keyword density
        kw_bonus = min(2.0, op.keyword_match * 0.5)
        # Recency bonus: within last 24h gets +1
        recency_bonus = 1.0 if op.recency_hours <= 24 else 0.0
        score = base + kw_bonus + recency_bonus
        return round(max(1.0, min(10.0, score)), 2)

    # ── Score combiner ────────────────────────────────────────────────────────

    @staticmethod
    def _combine_scores(raw_score: float, ai_score: float) -> float:
        """
        Combine raw TrendMonitor score (0-100) and Gemini score (1-10)
        into a single final_score on the 1-10 scale.

        Formula:
            raw_norm  = raw_score / 100 * 9 + 1   (maps 0-100 → 1-10)
            final     = 0.40 * raw_norm + 0.60 * ai_score
        The Gemini score has higher weight because it captures content quality.
        """
        raw_norm = (raw_score / 100.0) * 9.0 + 1.0
        final = 0.40 * raw_norm + 0.60 * ai_score
        return round(max(1.0, min(10.0, final)), 2)
