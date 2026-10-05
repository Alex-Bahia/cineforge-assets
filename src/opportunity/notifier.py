"""
OpportunityNotifier — sends high-value opportunity alerts via Telegram and Discord.

Telegram setup (one-time):
    1. Open Telegram and message @BotFather → /newbot
    2. Copy the API token BotFather gives you → TELEGRAM_BOT_TOKEN env var
    3. Start a chat with your new bot, or add it to a group/channel
    4. Get your chat_id:
       - Personal: message @userinfobot after starting the bot
       - Group/Channel: use https://api.telegram.org/bot<TOKEN>/getUpdates
         after sending a message to the group
    5. Set TELEGRAM_CHAT_ID env var to the numeric chat_id (e.g. "-1001234567890")

Discord setup (one-time):
    1. In Discord, open a channel → Edit Channel → Integrations → Webhooks
    2. Create a webhook → copy the URL → DISCORD_WEBHOOK_URL env var

Both channels are optional; the notifier skips gracefully if unconfigured.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import TYPE_CHECKING, Optional

import requests

if TYPE_CHECKING:
    from .database import ScoredOpportunity

log = logging.getLogger(__name__)

# Telegram Bot API base URL
TG_API = "https://api.telegram.org/bot{token}/{method}"

# Retry settings for HTTP calls
MAX_RETRIES = 3
RETRY_DELAY = 1.5


class OpportunityNotifier:
    """
    Sends opportunity alerts to Telegram and/or Discord.

    Usage:
        notifier = OpportunityNotifier()
        notifier.notify(op)         # sends to all configured channels
        notifier.notify_batch(ops)  # respects rate-limits between calls
    """

    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook_url: Optional[str] = None,
    ) -> None:
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.discord_webhook_url = discord_webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")

        self._telegram_ok = bool(self.telegram_token and self.telegram_chat_id)
        self._discord_ok = bool(self.discord_webhook_url)

        if not self._telegram_ok and not self._discord_ok:
            log.warning(
                "[Notifier] No notification channel configured. "
                "Set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID and/or DISCORD_WEBHOOK_URL."
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def notify(self, op: "ScoredOpportunity") -> dict[str, bool]:
        """
        Send an alert for one opportunity to all configured channels.
        Returns {"telegram": bool, "discord": bool}.
        """
        results: dict[str, bool] = {"telegram": False, "discord": False}

        if self._telegram_ok:
            results["telegram"] = self._send_telegram(op)

        if self._discord_ok:
            results["discord"] = self._send_discord(op)

        return results

    def notify_batch(
        self,
        opportunities: list["ScoredOpportunity"],
        inter_message_delay: float = 1.0,
    ) -> list[dict[str, bool]]:
        """
        Notify for each opportunity; pause between messages to avoid rate limits.
        Telegram allows ~30 messages/second to one chat; Discord allows 5/2s.
        A 1s delay is safe for both.
        """
        results = []
        for i, op in enumerate(opportunities):
            results.append(self.notify(op))
            if i < len(opportunities) - 1:
                time.sleep(inter_message_delay)
        return results

    def send_summary(self, total_found: int, high_value: int, run_duration_s: float) -> None:
        """Send a brief scan-summary message (called at the end of each scheduled run)."""
        text = (
            f"*CineForge Scan Completo* ✅\n"
            f"• Oportunidades encontradas: {total_found}\n"
            f"• Alto valor (score ≥7): {high_value}\n"
            f"• Duração: {run_duration_s:.0f}s\n"
        )
        if self._telegram_ok:
            self._telegram_request("sendMessage", {
                "chat_id": self.telegram_chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
        if self._discord_ok:
            self._discord_request({"content": text.replace("*", "**")})

    # ── Telegram ──────────────────────────────────────────────────────────────

    def _send_telegram(self, op: "ScoredOpportunity") -> bool:
        score_bar = _score_bar(op.final_score)
        titles_text = ""
        if op.title_variants:
            titles_text = "\n".join(
                f"  • {t}" for t in op.title_variants[:3]
            )
            titles_text = f"\n*Títulos sugeridos:*\n{titles_text}"

        message = (
            f"🔥 *NOVA OPORTUNIDADE DETECTADA*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"*Score:* {op.final_score:.1f}/10  {score_bar}\n"
            f"*Tópico:* {op.topic[:120]}\n"
            f"*Fonte:* {op.source}\n"
            f"*AI Score:* {op.ai_score:.1f}  |  *Raw:* {op.raw_score:.0f}/100\n"
        )
        if op.ai_reasoning:
            message += f"*Por quê:* {op.ai_reasoning[:200]}\n"
        if op.url:
            message += f"[🔗 Ver fonte]({op.url})\n"
        message += titles_text

        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        return self._telegram_request("sendMessage", payload)

    def _telegram_request(self, method: str, payload: dict) -> bool:
        url = TG_API.format(token=self.telegram_token, method=method)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True
                log.warning(
                    "[Notifier/Telegram] attempt %d — status %d: %s",
                    attempt, resp.status_code, resp.text[:200],
                )
            except requests.RequestException as exc:
                log.warning("[Notifier/Telegram] attempt %d — request error: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
        return False

    # ── Discord ───────────────────────────────────────────────────────────────

    def _send_discord(self, op: "ScoredOpportunity") -> bool:
        score_bar = _score_bar(op.final_score)
        color = _discord_color(op.final_score)

        embed = {
            "title": f"🔥 Nova Oportunidade — Score {op.final_score:.1f}/10  {score_bar}",
            "description": op.topic[:256],
            "color": color,
            "fields": [
                {"name": "Fonte", "value": op.source, "inline": True},
                {"name": "AI Score", "value": f"{op.ai_score:.1f}/10", "inline": True},
                {"name": "Raw Score", "value": f"{op.raw_score:.0f}/100", "inline": True},
            ],
            "footer": {"text": "CineForge Opportunity Scanner"},
        }

        if op.ai_reasoning:
            embed["fields"].append({
                "name": "Por quê pontuação alta",
                "value": op.ai_reasoning[:1024],
                "inline": False,
            })

        if op.title_variants:
            embed["fields"].append({
                "name": "Títulos sugeridos",
                "value": "\n".join(f"• {t}" for t in op.title_variants[:3]),
                "inline": False,
            })

        if op.url:
            embed["url"] = op.url

        payload = {"embeds": [embed]}
        return self._discord_request(payload)

    def _discord_request(self, payload: dict) -> bool:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.post(self.discord_webhook_url, json=payload, timeout=10)
                if resp.status_code in (200, 204):
                    return True
                log.warning(
                    "[Notifier/Discord] attempt %d — status %d: %s",
                    attempt, resp.status_code, resp.text[:200],
                )
            except requests.RequestException as exc:
                log.warning("[Notifier/Discord] attempt %d — request error: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
        return False


# ── Visual helpers ─────────────────────────────────────────────────────────────

def _score_bar(score: float, width: int = 10) -> str:
    """Visual bar: ████████░░ for score 8/10."""
    filled = round(score)
    empty = width - filled
    return "█" * filled + "░" * empty


def _discord_color(score: float) -> int:
    """Returns a hex color int based on score band."""
    if score >= 9:
        return 0xFF0000   # red — viral potential
    if score >= 7:
        return 0xFF6B00   # orange — high value
    if score >= 5:
        return 0xFFD700   # gold — medium
    return 0x808080       # grey — low
