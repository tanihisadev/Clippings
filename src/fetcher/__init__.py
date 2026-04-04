from src.fetcher.base import BaseFetcher
from src.fetcher.bbc import BBCFetcher
from src.fetcher.hackernews import HackerNewsFetcher
from src.fetcher.rss import RSSFetcher

FETCHER_MAP = {
    "rss": RSSFetcher,
    "hackernews": HackerNewsFetcher,
    "bbc": BBCFetcher,
}


def get_fetcher(source_type: str, **kwargs) -> BaseFetcher:
    """Factory function to get the appropriate fetcher."""
    fetcher_cls = FETCHER_MAP.get(source_type)
    if not fetcher_cls:
        available = ", ".join(FETCHER_MAP.keys())
        raise ValueError(f"Unknown source type: {source_type}. Available: {available}")
    return fetcher_cls(**kwargs)
