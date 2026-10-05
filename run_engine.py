#!/usr/bin/env python3
"""
CineForge Engine — entry point principal para produção em massa.

Uso:
  python run_engine.py                           # batch diário completo
  python run_engine.py --dry-run                 # simula sem gerar vídeos
  python run_engine.py --niche finance_dark      # só um nicho
  python run_engine.py --workers 4               # 4 vídeos em paralelo
  python run_engine.py --stats                   # mostra estado da fila
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run_engine")


async def _pipeline_stub(job) -> Path:
    """
    Placeholder do pipeline completo — substitua pela chamada real ao pipeline CineForge.
    Em produção, chama: run_full_pipeline(job.topic, job.channel_id, job.language, ...)
    """
    import time
    log.info("Pipeline executando job %s: %s (%s)", job.job_id, job.topic[:50], job.niche)
    # Simula tempo de processamento
    await asyncio.sleep(2)
    output = Path(f"output/videos/{job.job_id}_{job.niche}.mp4")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.touch()
    job.estimated_cost_usd = 25.0  # Kling 2.5 Turbo estimativa
    return output


async def main(args) -> None:
    from src.engine.channel_engine import ChannelEngine

    engine = ChannelEngine(max_workers=args.workers)

    if args.stats:
        stats = engine.get_queue_stats()
        print("\n📊 Estado da fila CineForge:")
        for key, val in stats.items():
            print(f"  {key}: {val}")
        return

    niches = [args.niche] if args.niche else None
    result = await engine.run_daily_batch(
        pipeline_fn=_pipeline_stub,
        niches=niches,
        dry_run=args.dry_run,
    )

    print("\n✅ Batch concluído:")
    for key, val in result.items():
        print(f"  {key}: {val}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CineForge Engine — produção em massa")
    parser.add_argument("--dry-run", action="store_true", help="Simula sem gerar vídeos")
    parser.add_argument("--niche", help="Nicho específico: dark, finance_dark, kids, tech, education")
    parser.add_argument("--workers", type=int, default=2, help="Número de vídeos em paralelo (padrão: 2)")
    parser.add_argument("--stats", action="store_true", help="Mostra estado da fila de jobs")
    args = parser.parse_args()

    asyncio.run(main(args))
