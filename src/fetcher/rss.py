import hashlib
import feedparser
from typing import List
from src.fetcher.base import BaseFetcher
from src.fetcher.models import Article


class RSSFetcher(BaseFetcher):
    """Fetch articles from generic RSS feeds."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    async def fetch(self, max_articles: int = 10) -> List[Article]:
        feed = feedparser.parse(self.url)
        articles = []

        for entry in feed.entries[:max_articles]:
            article_id = hashlib.md5(entry.get("link", entry.get("title", "")).encode()).hexdigest()[:12]
            content = entry.get("summary", entry.get("description", ""))

            published = None
            if hasattr(entry, "published_parsed"):
                from datetime import datetime
                published = datetime(*entry.published_parsed[:6])

            articles.append(Article(
                id=article_id,
                title=entry.get("title", ""),
                url=entry.get("link", ""),
                source=self.name,
                content=self._strip_html(content),
                published_at=published,
            ))

        return articles

    def _strip_html(self, text: str) -> str:
        import re
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:2000]
