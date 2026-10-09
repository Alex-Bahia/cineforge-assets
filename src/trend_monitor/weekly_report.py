"""
Weekly Opportunity Report — gera e envia relatório semanal de oportunidades.

Consolida dados de todos os nichos (dark, finance_dark, kids, tech, education)
e envia via Telegram ou salva como HTML/Markdown.

Uso:
  python -m src.trend_monitor.weekly_report
  python -m src.trend_monitor.weekly_report --output html --send-telegram
"""
import csv
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

BATCH_DIR = Path("batch")
REPORT_DIR = Path("reports")

NICHE_LABELS = {
    "finance_dark": "💰 Finance Dark (True Crime + Finanças)",
    "dark": "🔎 Dark (True Crime / Conspiração)",
    "kids": "🎨 Kids (Conteúdo Infantil)",
    "tech": "💻 Tech (Tecnologia / IA)",
    "education": "📚 Education (Educação)",
    "unknown": "❓ Sem nicho classificado",
}

NICHE_CPM = {
    "finance_dark": "$15–45",
    "dark": "$4–12",
    "kids": "$0.50–1.50",
    "tech": "$8–20",
    "education": "$5–15",
    "unknown": "$2–8",
}


def _read_csv_opportunities(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _filter_recent(rows: list[dict], days: int = 7) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = []
    for row in rows:
        # If there's no date field, include it
        fetched = row.get("fetched_at", "") or row.get("created_at", "")
        if not fetched:
            recent.append(row)
            continue
        try:
            dt = datetime.fromisoformat(fetched.replace("Z", "+00:00").replace("+00:00", ""))
            if dt >= cutoff:
                recent.append(row)
        except Exception:
            recent.append(row)
    return recent


def _group_by_niche(rows: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        niche = row.get("niche", "unknown") or "unknown"
        groups.setdefault(niche, []).append(row)
    # Sort each group by score descending
    for niche in groups:
        groups[niche].sort(key=lambda r: float(r.get("score", 0) or 0), reverse=True)
    return groups


def generate_markdown_report(days: int = 7) -> str:
    csv_path = BATCH_DIR / "topics.csv"
    rows = _read_csv_opportunities(csv_path)
    recent = _filter_recent(rows, days)
    groups = _group_by_niche(recent)

    total = len(recent)
    week_str = (datetime.utcnow() - timedelta(days=days)).strftime("%d/%m")
    today_str = datetime.utcnow().strftime("%d/%m/%Y")

    lines = [
        f"# 📊 Relatório Semanal CineForge",
        f"**Período:** {week_str} → {today_str}  |  **Total de oportunidades:** {total}",
        "",
        "---",
        "",
    ]

    # Summary table
    lines.append("## Resumo por Nicho")
    lines.append("")
    lines.append("| Nicho | Oportunidades | CPM Estimado | Top Score |")
    lines.append("|-------|--------------|-------------|-----------|")
    for niche, niche_rows in sorted(groups.items(), key=lambda x: float(x[1][0].get("score", 0) or 0) if x[1] else 0, reverse=True):
        label = NICHE_LABELS.get(niche, niche)
        cpm = NICHE_CPM.get(niche, "—")
        top_score = f"{float(niche_rows[0].get('score', 0) or 0):.2f}" if niche_rows else "—"
        lines.append(f"| {label} | {len(niche_rows)} | {cpm} | {top_score} |")
    lines.append("")

    # Top 5 overall
    top_overall = sorted(recent, key=lambda r: float(r.get("score", 0) or 0), reverse=True)[:5]
    if top_overall:
        lines.append("## 🏆 Top 5 Oportunidades da Semana")
        lines.append("")
        for i, row in enumerate(top_overall, 1):
            topic = row.get("topic", "—")
            score = float(row.get("score", 0) or 0)
            niche = row.get("niche", "unknown")
            source = row.get("source", "—")
            url = row.get("url", "")
            link = f" → [{url}]({url})" if url else ""
            lines.append(f"{i}. **{topic}**")
            lines.append(f"   - Score: `{score:.2f}` | Nicho: `{niche}` | Fonte: `{source}`{link}")
        lines.append("")

    # Detail per niche
    for niche, niche_rows in groups.items():
        label = NICHE_LABELS.get(niche, niche)
        lines.append(f"## {label}")
        lines.append(f"*{len(niche_rows)} oportunidades detectadas*")
        lines.append("")
        for row in niche_rows[:10]:
            topic = row.get("topic", "—")
            score = float(row.get("score", 0) or 0)
            source = row.get("source", "—")
            duration = row.get("duration_min", "?")
            url = row.get("url", "")
            link = f" | [fonte]({url})" if url else ""
            lines.append(f"- **{topic}**  ·  score `{score:.2f}` · {duration}min · {source}{link}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Gerado automaticamente pelo CineForge em {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*")

    return "\n".join(lines)


def generate_html_report(days: int = 7) -> str:
    md = generate_markdown_report(days)
    # Simple HTML wrapper — no external deps needed
    escaped = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CineForge Weekly Report</title>
<style>
  body {{ font-family: sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #222; }}
  pre {{ background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; }}
  h1 {{ color: #1a1a2e; }}
  h2 {{ color: #16213e; border-bottom: 2px solid #e94560; padding-bottom: 6px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #16213e; color: white; }}
  tr:nth-child(even) {{ background: #f9f9f9; }}
</style>
</head>
<body>
<pre>{escaped}</pre>
</body>
</html>"""
    return html


def send_telegram(text: str, token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """Send a message via Telegram Bot API (requires python-telegram-bot or requests)."""
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados — pulando envio")
        return False
    try:
        import urllib.request
        payload = json.dumps({"chat_id": chat_id, "text": text[:4096], "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        log.info("Relatório enviado via Telegram")
        return True
    except Exception as e:
        log.error("Erro ao enviar Telegram: %s", e)
        return False


def save_report(content: str, fmt: str = "md") -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"report_{datetime.utcnow().strftime('%Y%m%d')}.{fmt}"
    path = REPORT_DIR / filename
    path.write_text(content, encoding="utf-8")
    log.info("Relatório salvo em %s", path)
    return path


def run_weekly_report(
    days: int = 7,
    output: str = "md",
    send_tg: bool = False,
) -> Path:
    if output == "html":
        content = generate_html_report(days)
    else:
        content = generate_markdown_report(days)

    path = save_report(content, fmt=output)

    if send_tg:
        md_summary = generate_markdown_report(days)
        # Trim to fit Telegram's 4096 char limit
        send_telegram(md_summary[:4000])

    return path


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Gera relatório semanal CineForge")
    parser.add_argument("--days", type=int, default=7, help="Janela de dias (padrão: 7)")
    parser.add_argument("--output", choices=["md", "html"], default="md", help="Formato de saída")
    parser.add_argument("--send-telegram", action="store_true", help="Enviar via Telegram")
    args = parser.parse_args()

    path = run_weekly_report(days=args.days, output=args.output, send_tg=args.send_telegram)
    print(f"Relatório gerado: {path}")
