import litellm

from src.fetcher.models import Article


class ArticleSummarizer:
    """Summarize articles using LiteLLM (supports Ollama, OpenAI, Anthropic, etc.)."""

    SYSTEM_PROMPT = (
        "You are a news summarization assistant. "
        "Summarize each article in 2-3 sentences. "
        "Be concise, factual, and capture the key points. "
        "Do not add opinions or commentary."
    )

    USER_PROMPT = """Title: {title}
Content: {content}

Summary:"""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        api_key: str = "",
    ):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self._configure_litellm()

    def _configure_litellm(self) -> None:
        if self.api_key:
            litellm.api_key = self.api_key
        else:
            litellm.api_key = "not-needed"

    async def summarize(self, article: Article) -> Article:
        """Summarize a single article."""
        prompt = self.USER_PROMPT.format(
            title=article.title,
            content=article.content[:1500] if article.content else "No content available.",
        )

        response = await litellm.acompletion(
            model=f"openai/{self.model}",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.3,
            api_base=self.base_url if self.base_url else None,
        )

        article.summary = response.choices[0].message.content.strip()
        return article

    async def summarize_batch(self, articles: list[Article]) -> list[Article]:
        """Summarize multiple articles."""
        results = []
        for article in articles:
            try:
                summarized = await self.summarize(article)
                results.append(summarized)
            except Exception as e:
                print(f"Failed to summarize article '{article.title}': {e}")
                article.summary = f"[Summary unavailable: {e}]"
                results.append(article)
        return results
