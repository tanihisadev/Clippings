import httpx

from src.fetcher.models import Article
from src.notifier.base import BaseNotifier


class NtfyNotifier(BaseNotifier):
    """Send digest via ntfy.sh."""

    def __init__(self, ntfy_url: str, topic: str):
        self.ntfy_url = ntfy_url.rstrip("/")
        self.topic = topic

    async def send(self, groups: dict[str, dict[str, list[Article]]]) -> str:
        message = "📰 *Clippings*\n\n"

        for topic_name, sources in groups.items():
            message += f"*{topic_name}*\n"
            for source_name, articles in sources.items():
                message += f"  _{source_name}_\n"
                for article in articles:
                    summary_preview = article.summary[:100] if article.summary else "No summary"
                    message += f"  • {article.title}\n    {summary_preview}\n"
                    message += f"    {article.url}\n\n"

        payload = {
            "topic": self.topic,
            "message": message,
            "title": "Clippings",
            "tags": "newspaper",
            "actions": [
                {
                    "action": "view",
                    "label": "👍 Like",
                    "url": f"{self.ntfy_url}/{self.topic}?action=like",
                },
                {
                    "action": "view",
                    "label": "👎 Dislike",
                    "url": f"{self.ntfy_url}/{self.topic}?action=dislike",
                },
            ],
        }

        url = f"{self.ntfy_url}/{self.topic}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

        return "ntfy"
