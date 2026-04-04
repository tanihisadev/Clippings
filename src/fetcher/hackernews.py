import hashlib
import httpx
from datetime import datetime
from typing import List
from src.fetcher.base import BaseFetcher
from src.fetcher.models import Article


class HackerNewsFetcher(BaseFetcher):
    """Fetch top stories from Hacker News API."""

    API_BASE = "https://hacker-news.firebaseio.com/v0"

    async def fetch(self, max_articles: int = 10) -> List[Article]:
        async with httpx.AsyncClient() as client:
            top_ids = await self._get_top_ids(client, max_articles)
            articles = []

            for item_id in top_ids:
                item = await self._get_item(client, item_id)
                if not item or not item.get("url"):
                    continue

                article_id = hashlib.md5(str(item_id).encode()).hexdigest()[:12]
                published = None
                if item.get("time"):
                    published = datetime.fromtimestamp(item["time"])

                articles.append(Article(
                    id=article_id,
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    source="hackernews",
                    content=item.get("text", "") or "",
                    published_at=published,
                    metadata={"score": item.get("score", 0), "by": item.get("by", "")},
                ))

        return articles

    async def _get_top_ids(self, client: httpx.AsyncClient, count: int) -> List[int]:
        resp = await client.get(f"{self.API_BASE}/topstories.json")
        resp.raise_for_status()
        ids = resp.json()
        return ids[:count]

    async def _get_item(self, client: httpx.AsyncClient, item_id: int) -> dict:
        resp = await client.get(f"{self.API_BASE}/item/{item_id}.json")
        resp.raise_for_status()
        return resp.json()
