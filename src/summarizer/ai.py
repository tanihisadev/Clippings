import os

import litellm

from src.fetcher.models import Article

PROVIDER_MODEL_PREFIX = {
    "ollama": "ollama",
    "openai": "openai",
    "anthropic": "anthropic",
    "openai-compatible": "openai",
}


class ArticleSummarizer:
    """Summarize articles using LiteLLM (supports Ollama, llama.cpp, OpenAI, Anthropic, etc.)."""

    SYSTEM_PROMPT = (
        "Summarize this article in 1-2 sentences. Be concise and factual."
    )

    USER_PROMPT = """Title: {title}
Content: {content}

Summary:"""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        api_key: str = "",
        provider: str = "ollama",
    ):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.provider = provider
        self._configure_litellm()

    def _model_name(self) -> str:
        prefix = PROVIDER_MODEL_PREFIX.get(self.provider, "openai")
        return f"{prefix}/{self.model}"

    def _configure_litellm(self) -> None:
        if self.provider == "ollama":
            if self.base_url:
                os.environ["OLLAMA_API_BASE"] = self.base_url
            os.environ["OLLAMA_API_KEY"] = "not-needed"
        elif self.provider == "anthropic":
            if self.api_key:
                os.environ["ANTHROPIC_API_KEY"] = self.api_key
        elif self.provider in ("openai", "openai-compatible"):
            if self.base_url:
                os.environ["OPENAI_API_BASE"] = self.base_url
            if self.api_key:
                os.environ["OPENAI_API_KEY"] = self.api_key
            else:
                os.environ["OPENAI_API_KEY"] = "not-needed"

    async def summarize(self, article: Article) -> Article:
        """Summarize a single article."""
        prompt = self.USER_PROMPT.format(
            title=article.title,
            content=article.content[:1500] if article.content else "No content available.",
        )

        response = await litellm.acompletion(
            model=self._model_name(),
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=100,
            temperature=0.3,
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
