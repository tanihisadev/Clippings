import json
import os

import litellm

from src.fetcher.models import Article

PROVIDER_MODEL_PREFIX = {
    "ollama": "ollama",
    "openai": "openai",
    "anthropic": "anthropic",
    "openai-compatible": "openai",
}


class ArticleGrouper:
    """Group articles into fixed, user-defined categories."""

    def __init__(
        self,
        model: str = "llama3.1",
        base_url: str = "http://localhost:11434",
        api_key: str = "",
        categories: list[str] | None = None,
        provider: str = "ollama",
    ):
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.provider = provider
        self.categories = categories or [
            "Technology",
            "Science",
            "Politics",
            "Business",
            "Health",
            "Entertainment",
            "Sports",
            "Other",
        ]
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

    async def group(self, articles: list[Article]) -> dict[str, list[Article]]:
        """Assign each article to one of the fixed categories."""
        if not articles:
            return {}

        categories_str = ", ".join(self.categories)
        articles_list = "\n".join(
            f"- ID: {a.id}, Title: {a.title}, Source: {a.source}" for a in articles
        )

        system_prompt = (
            "You are a news categorization assistant. "
            "Assign each article to EXACTLY ONE of these categories:\n"
            f"{categories_str}\n\n"
            "Return ONLY valid JSON in this format:\n"
            '{"article_id": "Category", "article_id2": "Category2"}\n\n'
            "Use the exact category names listed above. "
            "Do not invent new categories. "
            "Do not include any explanation."
        )

        user_prompt = f"""Categorize these articles:

{articles_list}

Return only JSON mapping article IDs to category names."""

        response = await litellm.acompletion(
            model=self._model_name(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=500,
            temperature=0.1,
        )

        content = response.choices[0].message.content.strip()
        content = content.strip("```json").strip("```").strip()

        try:
            mapping = json.loads(content)
        except json.JSONDecodeError:
            return {"Other": articles}

        result = {cat: [] for cat in self.categories}
        article_map = {a.id: a for a in articles}

        for article_id, category in mapping.items():
            if article_id in article_map:
                if category in result:
                    article = article_map[article_id]
                    article.topic = category
                    result[category].append(article)
                else:
                    article = article_map[article_id]
                    article.topic = "Other"
                    result["Other"].append(article)

        for article in articles:
            if not article.topic:
                article.topic = "Other"
                result["Other"].append(article)

        result = {cat: arts for cat, arts in result.items() if arts}
        return result
