from src.fetcher.rss import RSSFetcher
from src.fetcher.hackernews import HackerNewsFetcher
from src.fetcher.bbc import BBCFetcher
from src.fetcher.base import BaseFetcher

FETCHER_MAP = {
    "rss": RSSFetcher,
    "hackernews": HackerNewsFetcher,
    "bbc": BBCFetcher,
}


def get_fetcher(source_type: str, **kwargs) -> BaseFetcher:
    """Factory function to get the appropriate fetcher."""
    fetcher_cls = FETCHER_MAP.get(source_type)
    if not fetcher_cls:
        raise ValueError(f"Unknown source type: {source_type}. Available: {list(FETCHER_MAP.keys())}")
    return fetcher_cls(**kwargs)
