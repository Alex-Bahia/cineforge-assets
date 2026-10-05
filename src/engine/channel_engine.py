"""
ChannelEngine — motor de produção em massa para múltiplos canais simultâneos.

Orquestra:
  1. Detecção de oportunidades (monitor/scanner por nicho)
  2. Criação de VideoJobs priorizados por score
  3. Execução do pipeline completo via JobQueue
  4. Upload automático com parâmetros por canal
  5. Relatório de performance

Suporta até N canais em paralelo, cada um com seu nicho, idioma e configuração.
"""
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .job_queue import JobQueue, VideoJob

log = logging.getLogger(__name__)


@dataclass
class ChannelConfig:
    """Configuração operacional de um canal para o engine."""
    channel_id: str
    niche: str
    language: str
    market: str
    max_videos_per_day: int = 3
    video_provider: str = "auto"
    tts_tier: str = "free"
    priority: int = 5
    enabled: bool = True


# Configurações padrão dos canais ativos — sincronizado com channel_profiles.py
DEFAULT_CHANNELS = [
    ChannelConfig("br_dark",          "dark",         "pt-BR", "BR", max_videos_per_day=3),
    ChannelConfig("br_finance_dark",  "finance_dark", "pt-BR", "BR", max_videos_per_day=2, priority=2),
    ChannelConfig("us_finance_dark",  "finance_dark", "en-US", "US", max_videos_per_day=2, priority=2),
    ChannelConfig("gb_finance_dark",  "finance_dark", "en-GB", "GB", max_videos_per_day=1, priority=3),
    ChannelConfig("br_kids",          "kids",         "pt-BR", "BR", max_videos_per_day=5, priority=4),
]


class ChannelEngine:
    """
    Motor central de produção em massa para múltiplos canais.

    Fluxo:
      1. scan_opportunities() — descobre tópicos com alto score
      2. create_jobs()        — converte oportunidades em VideoJobs
      3. queue.run()          — processa tudo com N workers em paralelo
    """

    def __init__(
        self,
        channels: Optional[list[ChannelConfig]] = None,
        max_workers: int = 2,
        queue_file: Optional[Path] = None,
    ):
        self.channels = {c.channel_id: c for c in (channels or DEFAULT_CHANNELS) if c.enabled}
        self.queue = JobQueue(
            max_workers=max_workers,
            state_file=queue_file or Path("batch/job_queue.json"),
        )

    async def scan_opportunities(
        self,
        niches: Optional[list[str]] = None,
        top_per_niche: int = 5,
    ) -> list[dict]:
        """
        Varre oportunidades para todos os nichos ativos.
        Retorna lista de dicts com topic, niche, score, language.
        """
        from src.trend_monitor.monitor import TrendMonitor
        from src.trend_monitor.kids_monitor import KidsOpportunityMonitor
        from src.trend_monitor.opportunity_router import get_opportunity_router

        router = get_opportunity_router()
        active_niches = niches or list({c.niche for c in self.channels.values()})
        all_opportunities = []

        for niche in active_niches:
            try:
                if niche == "kids":
                    monitor = KidsOpportunityMonitor()
                    ops = await monitor.scan()
                    for op in ops[:top_per_niche]:
                        config = router.route(op.topic, niche, "BR")
                        all_opportunities.append({
                            "topic": op.topic,
                            "niche": niche,
                            "score": op.score,
                            "language": "pt-BR",
                            "market": "BR",
                            "channel_id": config.get("profile_id", "br_kids"),
                            "duration_min": op.suggested_duration_min,
                        })
                else:
                    monitor = TrendMonitor()
                    ops = monitor.get_top_opportunities(niche=niche, limit=top_per_niche)
                    for op in ops:
                        channel = self._find_channel_for_niche(niche, op.get("language", "pt-BR"))
                        all_opportunities.append({
                            "topic": op.get("topic", ""),
                            "niche": niche,
                            "score": op.get("score", 0),
                            "language": op.get("language", "pt-BR"),
                            "market": op.get("market", "BR"),
                            "channel_id": channel,
                            "duration_min": op.get("duration_min", 10),
                        })
            except Exception as e:
                log.warning("ChannelEngine: erro ao varrer nicho %s: %s", niche, e)

        # Sort by score descending
        all_opportunities.sort(key=lambda x: x.get("score", 0), reverse=True)
        log.info("ChannelEngine: %d oportunidades encontradas em %d nichos", len(all_opportunities), len(active_niches))
        return all_opportunities

    def _find_channel_for_niche(self, niche: str, language: str) -> str:
        for ch in self.channels.values():
            if ch.niche == niche and ch.language == language:
                return ch.channel_id
        for ch in self.channels.values():
            if ch.niche == niche:
                return ch.channel_id
        return list(self.channels.keys())[0]

    def create_jobs_from_opportunities(self, opportunities: list[dict]) -> list[VideoJob]:
        jobs = []
        for op in opportunities:
            channel_id = op.get("channel_id", "")
            channel = self.channels.get(channel_id)
            if not channel:
                channel = next(iter(self.channels.values()))

            job = VideoJob(
                topic=op["topic"],
                niche=op["niche"],
                language=op.get("language", channel.language),
                market=op.get("market", channel.market),
                channel_id=channel.channel_id,
                duration_min=op.get("duration_min", 10),
                tts_tier=channel.tts_tier,
                video_provider=channel.video_provider,
                priority=channel.priority,
                opportunity_score=op.get("score", 0.0),
            )
            jobs.append(job)
        return jobs

    async def run_daily_batch(
        self,
        pipeline_fn,
        niches: Optional[list[str]] = None,
        dry_run: bool = False,
    ) -> dict:
        """
        Executa o batch diário completo:
          1. Scan de oportunidades
          2. Cria jobs limitados por max_videos_per_day por canal
          3. Processa tudo na fila
        """
        log.info("ChannelEngine: iniciando batch diário")
        opportunities = await self.scan_opportunities(niches=niches)

        # Limit by channel daily quota
        channel_counts: dict[str, int] = {}
        selected = []
        for op in opportunities:
            ch_id = op.get("channel_id", "")
            channel = self.channels.get(ch_id)
            limit = channel.max_videos_per_day if channel else 1
            count = channel_counts.get(ch_id, 0)
            if count < limit:
                selected.append(op)
                channel_counts[ch_id] = count + 1

        log.info("ChannelEngine: %d oportunidades selecionadas para produção hoje", len(selected))

        if dry_run:
            return {"dry_run": True, "selected": selected, "total": len(selected)}

        jobs = self.create_jobs_from_opportunities(selected)
        self.queue.add_batch(jobs)
        await self.queue.run(pipeline_fn=pipeline_fn)

        return self.queue.get_stats()

    def get_queue_stats(self) -> dict:
        return self.queue.get_stats()
