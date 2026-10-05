#!/usr/bin/env python3
"""
Entry point standalone para o KidsOpportunityMonitor.

Executa varredura de oportunidades para conteúdo infantil e grava em batch/topics.csv.

Uso:
  python run_kids_monitor.py
  python run_kids_monitor.py --top 20
  python run_kids_monitor.py --export json
"""
import argparse
import asyncio
import csv
import json
import logging
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent))

from src.trend_monitor.kids_monitor import KidsOpportunityMonitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("run_kids_monitor")


async def main(top: int = 15, export: str = "csv") -> None:
    monitor = KidsOpportunityMonitor()
    log.info("Iniciando KidsOpportunityMonitor…")
    opportunities = await monitor.scan()

    if not opportunities:
        log.warning("Nenhuma oportunidade encontrada.")
        return

    log.info("Top %d oportunidades kids:", min(top, len(opportunities)))
    for i, op in enumerate(opportunities[:top], 1):
        print(f"  {i:2d}. [{op.score:.2f}] {op.topic}")
        print(f"       CPM: {op.cpm_estimate} | busca/mês: {op.monthly_searches:,} | comp: {op.competition_level}")

    if export == "csv":
        monitor.export_to_csv(opportunities)
        log.info("Exportado para batch/topics.csv")
    elif export == "json":
        Path("batch").mkdir(exist_ok=True)
        out = Path("batch/kids_opportunities.json")
        data = [
            {
                "topic": op.topic,
                "score": op.score,
                "cpm_estimate": op.cpm_estimate,
                "monthly_searches": op.monthly_searches,
                "competition_level": op.competition_level,
                "niche": op.niche,
                "tone": op.tone,
                "suggested_duration_min": op.suggested_duration_min,
                "tags": op.tags,
                "url": op.url,
                "source": op.source,
            }
            for op in opportunities
        ]
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        log.info("Exportado para %s", out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Varredura de oportunidades para canais kids")
    parser.add_argument("--top", type=int, default=15, help="Quantas oportunidades exibir (padrão: 15)")
    parser.add_argument("--export", choices=["csv", "json", "none"], default="csv", help="Formato de exportação")
    args = parser.parse_args()
    asyncio.run(main(top=args.top, export=args.export))
