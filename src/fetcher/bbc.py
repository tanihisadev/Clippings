from src.fetcher.rss import RSSFetcher


class BBCFetcher(RSSFetcher):
    """Fetch articles from BBC News RSS feed."""

    def __init__(self, name: str = "BBC News", url: str = "http://feeds.bbci.co.uk/news/rss.xml"):
        super().__init__(name, url)
