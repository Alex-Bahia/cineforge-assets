#!/usr/bin/env python3
"""
Entry point para geração e envio do relatório semanal CineForge.

Uso:
  python run_weekly_report.py
  python run_weekly_report.py --output html
  python run_weekly_report.py --send-telegram
  python run_weekly_report.py --days 14 --output html --send-telegram
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.trend_monitor.weekly_report import run_weekly_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera relatório semanal CineForge")
    parser.add_argument("--days", type=int, default=7, help="Janela de dias (padrão: 7)")
    parser.add_argument("--output", choices=["md", "html"], default="md", help="Formato de saída")
    parser.add_argument("--send-telegram", action="store_true", help="Enviar resumo via Telegram")
    args = parser.parse_args()

    path = run_weekly_report(days=args.days, output=args.output, send_tg=args.send_telegram)
    print(f"\n✅ Relatório gerado: {path}")
    if args.output == "md":
        print("\n--- PRÉVIA ---")
        print(path.read_text(encoding="utf-8")[:2000])
