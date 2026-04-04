import httpx
from typing import Dict, List
from src.notifier.base import BaseNotifier
from src.fetcher.models import Article


class DiscordNotifier(BaseNotifier):
    """Send digest via Discord webhook."""

    def __init__(self, webhook_url: str, ping: str = ""):
        self.webhook_url = webhook_url
        self.ping = ping

    def _ping_text(self) -> str:
        if self.ping == "everyone":
            return "@everyone "
        elif self.ping == "here":
            return "@here "
        elif self.ping.startswith("<@") or self.ping.startswith("<@&"):
            return f"{self.ping} "
        return ""

    async def send(self, groups: Dict[str, Dict[str, List[Article]]]) -> str:
        embeds = []

        for topic, sources in groups.items():
            source_text = ""
            for source_name, articles in sources.items():
                source_text += f"\n**{source_name}**\n"
                for article in articles:
                    summary_preview = article.summary[:150] if article.summary else "No summary"
                    source_text += f"• [{article.title}]({article.url})\n  _{summary_preview}_\n\n"

            embed = {
                "title": f"📰 {topic}",
                "description": source_text[:4096],
                "color": 0x5865F2,
            }
            embeds.append(embed)

        if not embeds:
            embeds = [{"title": "Clippings", "description": "No articles found.", "color": 0x5865F2}]

        ping = self._ping_text()
        payload = {
            "content": f"{ping}**Clippings** 👍/👎 react to train your preferences",
            "embeds": embeds,
            "allowed_mentions": {
                "parse": ["everyone", "users", "roles"],
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.webhook_url, json=payload)
            resp.raise_for_status()

        return "discord"
