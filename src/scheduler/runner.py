import json
from datetime import datetime
from pathlib import Path

import httpx
import trafilatura

from src.config import Config
from src.fetcher import get_fetcher
from src.fetcher.models import Article
from src.grouper.topic import ArticleGrouper
from src.notifier import get_notifier
from src.storage.json_store import JSONStore
from src.summarizer.ai import ArticleSummarizer


class DigestRunner:
    """Orchestrates the full digest pipeline: fetch -> summarize -> group -> notify."""

    CACHE_FILE = "data/digest_cache.json"

    def __init__(self, config: Config):
        self.config = config
        self.store = JSONStore()

    async def run(self, use_cache: bool = False) -> None:
        """Execute the full digest pipeline."""
        print("Starting digest pipeline...")

        if use_cache:
            groups = self._load_cache()
            if groups:
                print("Loaded cached digest, retrying notification...")
                await self._send(groups)
                return
            print("No cache found, running full pipeline")

        articles = await self._fetch_all()
        print(f"Fetched {len(articles)} articles")

        articles = self._deduplicate(articles)
        print(f"After dedup: {len(articles)} articles")

        articles = await self._fetch_content(articles)
        print(f"Fetched content for {sum(1 for a in articles if a.content)} articles")

        articles = self._score_articles(articles)
        articles.sort(key=lambda a: a.score, reverse=True)

        max_articles = self.config.schedule.max_articles
        articles = articles[:max_articles]

        if not articles:
            print("No articles to process")
            return

        summarizer = ArticleSummarizer(
            model=self.config.ai.model,
            base_url=self.config.ai.base_url,
            api_key=self.config.ai.api_key,
        )
        articles = await summarizer.summarize_batch(articles)
        print("Summarization complete")

        grouper = ArticleGrouper(
            model=self.config.ai.model,
            base_url=self.config.ai.base_url,
            api_key=self.config.ai.api_key,
            categories=self.config.categories,
        )
        groups_raw = await grouper.group(articles)

        groups = {}
        for topic, topic_articles in groups_raw.items():
            by_source = {}
            for article in topic_articles:
                if article.source not in by_source:
                    by_source[article.source] = []
                by_source[article.source].append(article)
            groups[topic] = by_source

        print(f"Grouped into {len(groups)} topics")

        self._save_cache(groups, articles)
        await self._send(groups)

    async def _send(self, groups: dict) -> None:
        """Send digest via notifier, with retry on failure."""
        notifier = self._create_notifier()
        if notifier:
            try:
                message_id = await notifier.send(groups)
                print(f"Digest sent via {self.config.notifier.type}")

                all_articles = [
                    a for topic in groups.values() for articles in topic.values() for a in articles
                ]
                source_names = list(set(a.source for a in all_articles))
                self.store.record_digest(len(all_articles), source_names, message_id)
                self._clear_cache()
            except Exception as e:
                print(f"\nNotification failed: {e}")
                print(f"Digest saved to cache ({self.CACHE_FILE}). Run 'digest resend' to retry.")
        else:
            self._print_digest(groups)
            all_articles = [
                a for topic in groups.values() for articles in topic.values() for a in articles
            ]
            source_names = list(set(a.source for a in all_articles))
            self.store.record_digest(len(all_articles), source_names, "console")
            self._clear_cache()

    def _article_to_dict(self, article: Article) -> dict:
        return {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": article.source,
            "content": article.content,
            "summary": article.summary,
            "topic": article.topic,
            "score": article.score,
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "metadata": article.metadata,
        }

    def _dict_to_article(self, d: dict) -> Article:
        from datetime import datetime

        published = None
        if d.get("published_at"):
            try:
                published = datetime.fromisoformat(d["published_at"])
            except (ValueError, TypeError):
                pass
        return Article(
            id=d["id"],
            title=d["title"],
            url=d["url"],
            source=d["source"],
            content=d.get("content", ""),
            summary=d.get("summary", ""),
            topic=d.get("topic", ""),
            score=d.get("score", 0),
            published_at=published,
            metadata=d.get("metadata", {}),
        )

    def _save_cache(self, groups: dict, articles: list[Article]) -> None:
        """Save processed digest to cache for retry."""
        Path("data").mkdir(parents=True, exist_ok=True)
        cache = {
            "timestamp": datetime.utcnow().isoformat(),
            "articles": [self._article_to_dict(a) for a in articles],
            "groups": {
                topic: {
                    source: [self._article_to_dict(a) for a in arts]
                    for source, arts in sources.items()
                }
                for topic, sources in groups.items()
            },
        }
        with open(self.CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
        print(f"Digest cached to {self.CACHE_FILE}")

    def _load_cache(self) -> dict:
        """Load cached digest groups."""
        path = Path(self.CACHE_FILE)
        if not path.exists():
            return {}
        with open(path) as f:
            cache = json.load(f)
        groups = {}
        for topic, sources in cache.get("groups", {}).items():
            groups[topic] = {}
            for source, arts in sources.items():
                groups[topic][source] = [self._dict_to_article(a) for a in arts]
        return groups

    def _clear_cache(self) -> None:
        """Remove cache after successful send."""
        path = Path(self.CACHE_FILE)
        if path.exists():
            path.unlink()

    async def _fetch_all(self) -> list[Article]:
        """Fetch articles from all configured sources."""
        import traceback

        all_articles = []
        for source in self.config.sources:
            try:
                print(f"  Fetching from {source.name} ({source.type})...")
                if source.type == "hackernews":
                    fetcher = get_fetcher(source.type)
                elif source.type == "bbc":
                    fetcher = get_fetcher(source.type, name=source.name, url=source.url)
                else:
                    fetcher = get_fetcher(source.type, name=source.name, url=source.url)

                articles = await fetcher.fetch(source.max_articles)
                print(f"  Got {len(articles)} from {source.name}")
                all_articles.extend(articles)
            except Exception:
                print(f"  Error fetching from {source.name}:")
                traceback.print_exc()

        return all_articles

    def _deduplicate(self, articles: list[Article]) -> list[Article]:
        """Remove duplicate articles by URL."""
        seen = set()
        unique = []
        for article in articles:
            if article.url not in seen:
                seen.add(article.url)
                unique.append(article)
        return unique

    async def _fetch_content(self, articles: list[Article]) -> list[Article]:
        """Fetch article content from URLs for articles with no body text."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            tasks = []
            for article in articles:
                if not article.content or len(article.content) < 100:
                    tasks.append(self._extract_article(client, article))
                else:
                    tasks.append(None)

            results = []
            for i, article in enumerate(articles):
                if tasks[i]:
                    results.append(await tasks[i])
                else:
                    results.append(article)
        return results

    async def _extract_article(self, client: httpx.AsyncClient, article: Article) -> Article:
        """Fetch and extract readable text from a URL."""
        try:
            resp = await client.get(article.url, follow_redirects=True)
            resp.raise_for_status()
            text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
            if text:
                article.content = text[:3000]
        except Exception as e:
            print(f"  Failed to fetch content for '{article.title}': {e}")
        return article

    def _score_articles(self, articles: list[Article]) -> list[Article]:
        """Score articles based on user preferences."""
        for article in articles:
            score = 0
            score += self.store.get_feedback_score(article.source, article.topic)

            if article.source in self.config.preferences.liked_sources:
                score += 3
            if article.source in self.config.preferences.disliked_sources:
                score -= 3

            if article.topic in self.config.preferences.liked_categories:
                score += 3
            if article.topic in self.config.preferences.disliked_categories:
                score -= 3

            article.score = score
        return articles

    def _create_notifier(self):
        """Create the appropriate notifier based on config."""
        n = self.config.notifier
        if n.type == "discord":
            if not n.webhook_url:
                return None
            return get_notifier(
                "discord",
                webhook_url=n.webhook_url,
                ping=getattr(n, "discord_ping", ""),
            )
        elif n.type == "ntfy":
            if not n.ntfy_topic:
                return None
            return get_notifier(
                "ntfy",
                ntfy_url=n.ntfy_url,
                topic=n.ntfy_topic,
            )
        elif n.type == "telegram":
            if not n.telegram_bot_token or not n.telegram_chat_id:
                return None
            return get_notifier(
                "telegram",
                bot_token=n.telegram_bot_token,
                chat_id=n.telegram_chat_id,
            )
        else:
            raise ValueError(f"Unknown notifier type: {n.type}")

    def _print_digest(self, groups: dict) -> None:
        """Print digest to console (fallback when notifier not configured)."""
        print("\n" + "=" * 60)
        print("DAILY NEWS DIGEST")
        print("=" * 60)

        for topic, sources in groups.items():
            print(f"\n{'─' * 40}")
            print(f"  {topic.upper()}")
            print(f"{'─' * 40}")
            for source_name, articles in sources.items():
                print(f"\n  [{source_name}]")
                for article in articles:
                    print(f"  • {article.title}")
                    if article.summary:
                        print(f"    {article.summary}")
                    print(f"    {article.url}\n")

        print("=" * 60)
