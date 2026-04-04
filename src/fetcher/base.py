from abc import ABC, abstractmethod
from typing import List
from src.fetcher.models import Article


class BaseFetcher(ABC):
    """Abstract base class for all news source fetchers."""

    @abstractmethod
    async def fetch(self, max_articles: int = 10) -> List[Article]:
        """Fetch articles from the source. Returns a list of Article objects."""
        pass
