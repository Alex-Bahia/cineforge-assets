"""
KidsOpportunityMonitor — Monitoramento de oportunidades para o nicho kids.

Diferente do TrendMonitor principal (focado em dark/crime/finanças), este
monitor foca em conteúdo evergreen educacional para crianças.

Características:
  - Score baseado em lifetime value (longevidade), não recência
  - Temas evergreen pré-mapeados com CPM e volume de buscas BR
  - Google Autocomplete para detectar tendências emergentes
  - YouTube RSS de canais kids referência
  - CPM BR kids: $0.50–$1.50 (compensado por volume e longevidade)
  - Gap real: conteúdo kids educacional PT-BR de qualidade é escasso

Usage:
    from src.trend_monitor.kids_monitor import KidsOpportunityMonitor

    monitor = KidsOpportunityMonitor()
    results = monitor.run()
    monitor.export_to_csv(results)
"""

from __future__ import annotations

import asyncio
import csv
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiohttp

log = logging.getLogger(__name__)

# ── Evergreen topics mapeados com dados de volume BR ─────────────────────────
EVERGREEN_KIDS_PT = [
    {"topic": "Aprendendo as Cores em Português — Vídeo Educativo para Bebês",
     "cpm_est": 1.20, "monthly_searches": 12000, "competition": "medium",
     "tone": "educativo e divertido", "duration_min": 4,
     "tags": ["cores", "bebês", "educativo", "português"]},
    {"topic": "Números 1 a 10 para Bebês — Animação Educativa em Português",
     "cpm_est": 1.10, "monthly_searches": 9500, "competition": "high",
     "tone": "educativo e musical", "duration_min": 4,
     "tags": ["números", "bebês", "animação", "contar"]},
    {"topic": "Alfabeto Completo A a Z em Português para Crianças",
     "cpm_est": 1.00, "monthly_searches": 8000, "competition": "high",
     "tone": "educativo e animado", "duration_min": 5,
     "tags": ["alfabeto", "letras", "crianças", "educativo"]},
    {"topic": "Animais da Fazenda para Crianças — Sons e Nomes em Português",
     "cpm_est": 1.15, "monthly_searches": 7500, "competition": "medium",
     "tone": "divertido e educativo", "duration_min": 4,
     "tags": ["animais", "fazenda", "sons", "crianças"]},
    {"topic": "Formas Geométricas para Bebês — Círculo, Quadrado, Triângulo",
     "cpm_est": 1.20, "monthly_searches": 5000, "competition": "low",
     "tone": "educativo e colorido", "duration_min": 4,
     "tags": ["formas", "geométricas", "bebês", "shapes"]},
    {"topic": "Emoções para Crianças — Feliz, Triste, Bravo, Surpreso",
     "cpm_est": 1.30, "monthly_searches": 4500, "competition": "low",
     "tone": "emocional e educativo", "duration_min": 4,
     "tags": ["emoções", "sentimentos", "crianças", "educativo"]},
    {"topic": "Números de 11 a 20 em Português para Crianças",
     "cpm_est": 1.10, "monthly_searches": 4000, "competition": "low",
     "tone": "educativo e musical", "duration_min": 4,
     "tags": ["números", "11 a 20", "crianças", "contar"]},
    {"topic": "Frutas em Português para Bebês Aprenderem — Coloridas e Animadas",
     "cpm_est": 1.15, "monthly_searches": 3800, "competition": "low",
     "tone": "divertido e educativo", "duration_min": 4,
     "tags": ["frutas", "bebês", "vocabulário", "colorido"]},
    {"topic": "Dias da Semana em Português — Música Infantil Educativa",
     "cpm_est": 1.10, "monthly_searches": 3500, "competition": "low",
     "tone": "musical e educativo", "duration_min": 3,
     "tags": ["dias da semana", "música infantil", "educativo", "semana"]},
    {"topic": "Cores do Arco-Íris para Crianças — As 7 Cores",
     "cpm_est": 1.20, "monthly_searches": 3200, "competition": "low",
     "tone": "colorido e divertido", "duration_min": 4,
     "tags": ["arco-íris", "cores", "crianças", "7 cores"]},
    {"topic": "Animais do Zoológico para Crianças — Leão, Elefante, Girafa",
     "cpm_est": 1.15, "monthly_searches": 3000, "competition": "low",
     "tone": "divertido e educativo", "duration_min": 5,
     "tags": ["zoológico", "animais", "crianças", "leão"]},
    {"topic": "Veículos para Bebês — Carro, Ônibus, Avião, Trem",
     "cpm_est": 1.10, "monthly_searches": 2800, "competition": "low",
     "tone": "divertido e educativo", "duration_min": 4,
     "tags": ["veículos", "carro", "ônibus", "bebês"]},
    {"topic": "Números 1 a 20 Completo em Português para Crianças",
     "cpm_est": 1.15, "monthly_searches": 2500, "competition": "low",
     "tone": "educativo e musical", "duration_min": 5,
     "tags": ["números 1 a 20", "completo", "crianças", "contar"]},
    {"topic": "Cores Primárias e Secundárias para Crianças",
     "cpm_est": 1.20, "monthly_searches": 2000, "competition": "low",
     "tone": "educativo e colorido", "duration_min": 4,
     "tags": ["cores primárias", "secundárias", "crianças", "misturar cores"]},
    {"topic": "Dinossauros para Crianças — Nomes e Curiosidades em Português",
     "cpm_est": 1.25, "monthly_searches": 2000, "competition": "medium",
     "tone": "empolgante e educativo", "duration_min": 6,
     "tags": ["dinossauros", "crianças", "rex", "nomes"]},
]

# ── Seeds para Google Autocomplete ────────────────────────────────────────────
KIDS_AUTOCOMPLETE_SEEDS = [
    "aprenda cores em português",
    "números para crianças em português",
    "alfabeto infantil animado",
    "animais para bebês",
    "músicas infantis em português",
    "formas para bebês aprenderem",
]

# ── Canais kids BR de referência (IDs para RSS) ───────────────────────────────
KIDS_REFERENCE_CHANNELS = [
    # Adicionar IDs após pesquisa: (channel_id, nome)
    # ("UCxxxxxx", "Galinha Pintadinha"),
    # ("UCyyyyyy", "Mundo Bita"),
]


@dataclass
class KidsOpportunity:
    """Oportunidade de conteúdo para o nicho kids."""
    topic: str
    source: str
    score: float = 0.0
    cpm_estimate: float = 1.0
    monthly_searches: int = 0
    competition_level: str = "unknown"  # low | medium | high | unknown
    niche: str = "kids"
    tone: str = "educativo e divertido"
    suggested_duration_min: int = 4
    tags: list = field(default_factory=list)
    url: str = ""
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class KidsOpportunityMonitor:
    """
    Monitor de oportunidades para o nicho kids/educacional infantil.

    Foca em temas evergreen (não dependem de timing) com alto volume
    de buscas acumulado ao longo de meses e anos.
    """

    def __init__(
        self,
        output_dir: str = "batch",
        top_n: int = 20,
    ):
        self.output_dir = Path(output_dir)
        self.top_n = top_n

    def run(self) -> list[KidsOpportunity]:
        """Executa todas as fontes e retorna oportunidades ranqueadas."""
        return asyncio.run(self._run_async())

    async def _run_async(self) -> list[KidsOpportunity]:
        tasks = [
            self._fetch_evergreen_topics(),
            self._fetch_google_autocomplete(),
            self._fetch_youtube_rss(),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_ops: list[KidsOpportunity] = []
        for r in results:
            if isinstance(r, Exception):
                log.warning("[KidsMonitor] Source error: %s", r)
            else:
                all_ops.extend(r)

        scored = [self._score(op) for op in all_ops]
        scored.sort(key=lambda o: o.score, reverse=True)
        log.info("[KidsMonitor] %d opportunities scored.", len(scored))
        return scored[: self.top_n]

    async def _fetch_evergreen_topics(self) -> list[KidsOpportunity]:
        """Retorna tópicos evergreen pré-mapeados."""
        ops = []
        for item in EVERGREEN_KIDS_PT:
            ops.append(KidsOpportunity(
                topic=item["topic"],
                source="evergreen_database",
                cpm_estimate=item["cpm_est"],
                monthly_searches=item["monthly_searches"],
                competition_level=item["competition"],
                tone=item.get("tone", "educativo e divertido"),
                suggested_duration_min=item.get("duration_min", 4),
                tags=item.get("tags", []),
            ))
        return ops

    async def _fetch_google_autocomplete(self) -> list[KidsOpportunity]:
        """Busca sugestões do Google para seeds kids."""
        BASE = "https://suggestqueries.google.com/complete/search"
        ops: list[KidsOpportunity] = []
        seen: set[str] = set()
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            for seed in KIDS_AUTOCOMPLETE_SEEDS[:4]:
                params = {"client": "firefox", "q": seed, "hl": "pt-BR", "gl": "BR"}
                try:
                    async with session.get(
                        BASE, params=params,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as resp:
                        if resp.status == 200:
                            payload = await resp.json(content_type=None)
                            suggestions = payload[1] if len(payload) > 1 else []
                            for sug in suggestions:
                                if sug not in seen and len(sug) > 15:
                                    seen.add(sug)
                                    ops.append(KidsOpportunity(
                                        topic=sug,
                                        source="google_autocomplete_kids",
                                        cpm_estimate=1.0,
                                        competition_level="unknown",
                                    ))
                    await asyncio.sleep(0.5)
                except Exception as exc:
                    log.debug("[KidsMonitor] Autocomplete '%s': %s", seed, exc)
        log.info("[KidsMonitor] Autocomplete: %d suggestions", len(ops))
        return ops

    async def _fetch_youtube_rss(self) -> list[KidsOpportunity]:
        """Monitora canais kids via RSS (sem API key)."""
        if not KIDS_REFERENCE_CHANNELS:
            return []
        ops: list[KidsOpportunity] = []
        try:
            import feedparser
        except ImportError:
            log.debug("[KidsMonitor] feedparser not installed, skipping RSS")
            return []
        async with aiohttp.ClientSession() as session:
            for channel_id, name in KIDS_REFERENCE_CHANNELS:
                url = (
                    f"https://www.youtube.com/feeds/videos.xml"
                    f"?channel_id={channel_id}"
                )
                try:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=8)
                    ) as resp:
                        if resp.status != 200:
                            continue
                        feed = feedparser.parse(await resp.text())
                    for entry in feed.entries[:5]:
                        title = entry.get("title", "")
                        if title:
                            ops.append(KidsOpportunity(
                                topic=f"[Tendência {name}] {title}",
                                source=f"youtube_rss/{name}",
                                url=entry.get("link", ""),
                                cpm_estimate=1.0,
                            ))
                except Exception as exc:
                    log.debug("[KidsMonitor] RSS %s: %s", name, exc)
        return ops

    def _score(self, op: KidsOpportunity) -> KidsOpportunity:
        """
        Score para kids usa lifetime value, não recência.

        Componentes:
          base (40p)  = log10(monthly_searches + 1) / log10(50000) * 40
          cpm  (20p)  = min(1.0, cpm_estimate / 1.50) * 20
          comp (30p)  = low:30 | medium:20 | high:10 | unknown:15
          src  (10p)  = evergreen:10 | outros:5
        """
        base = math.log10(op.monthly_searches + 1) / math.log10(50_000) * 40
        cpm_c = min(1.0, op.cpm_estimate / 1.50) * 20
        comp_map = {"low": 30, "medium": 20, "high": 10, "unknown": 15}
        comp = comp_map.get(op.competition_level, 15)
        src_bonus = 10 if "evergreen" in op.source else 5
        op.score = round(base + cpm_c + comp + src_bonus, 2)
        return op

    def export_to_csv(
        self,
        opportunities: list[KidsOpportunity],
        top_n: Optional[int] = None,
        csv_path: Optional[str] = None,
    ) -> str:
        """Appends kids opportunities to batch/topics.csv."""
        path = Path(csv_path) if csv_path else (self.output_dir / "topics.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = ["topic", "tone", "duration_min", "source", "score", "url", "status", "niche"]

        existing: set[str] = set()
        if path.exists():
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    existing.add(row.get("topic", "").strip().lower())

        ops = opportunities[: top_n] if top_n else opportunities
        new_rows = []
        for op in ops:
            if op.topic.lower() not in existing:
                new_rows.append({
                    "topic": op.topic,
                    "tone": op.tone,
                    "duration_min": op.suggested_duration_min,
                    "source": op.source,
                    "score": op.score,
                    "url": op.url,
                    "status": "pending",
                    "niche": "kids",
                })
                existing.add(op.topic.lower())

        write_header = not path.exists()
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if write_header:
                writer.writeheader()
            writer.writerows(new_rows)

        log.info("[KidsMonitor] Exported %d new opportunities to %s", len(new_rows), path)
        return str(path)
