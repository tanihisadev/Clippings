import httpx
from typing import Dict, List
from src.notifier.base import BaseNotifier
from src.fetcher.models import Article


class TelegramNotifier(BaseNotifier):
    """Send digest via Telegram Bot API."""

    API_BASE = "https://api.telegram.org/bot{token}"

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def send(self, groups: Dict[str, Dict[str, List[Article]]]) -> str:
        message = "📰 *Clippings*\n\n"

        for topic_name, sources in groups.items():
            message += f"*{topic_name}*\n"
            for source_name, articles in sources.items():
                message += f"  _{source_name}_\n"
                for article in articles:
                    summary_preview = article.summary[:100] if article.summary else "No summary"
                    title = article.title.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]")
                    message += f"  • [{title}]({article.url})\n    _{summary_preview}_\n\n"

        inline_keyboard = []
        row = []
        for topic_name in groups.keys():
            row.append({"text": f"👍 {topic_name}", "callback_data": f"like:{topic_name}"})
            row.append({"text": f"👎 {topic_name}", "callback_data": f"dislike:{topic_name}"})
            inline_keyboard.append(row)
            row = []

        url = f"{self.API_BASE.format(token=self.bot_token)}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message[:4096],
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": True,
            "reply_markup": {"inline_keyboard": inline_keyboard[:5]},
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

        return "telegram"
