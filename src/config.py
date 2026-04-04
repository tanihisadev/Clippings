import yaml
from pathlib import Path
from typing import List, Optional


class AIConfig:
    def __init__(
        self,
        provider: str = "ollama",
        base_url: str = "http://localhost:11434",
        model: str = "llama3.1",
        api_key: str = "",
    ):
        self.provider = provider
        self.base_url = base_url
        self.model = model
        self.api_key = api_key


class SourceConfig:
    def __init__(
        self,
        type: str,
        name: str,
        url: Optional[str] = None,
        max_articles: int = 10,
    ):
        self.type = type
        self.name = name
        self.url = url
        self.max_articles = max_articles


class ScheduleConfig:
    def __init__(self, time: str = "08:00", timezone: str = "UTC", max_articles: int = 20):
        self.time = time
        self.timezone = timezone
        self.max_articles = max_articles


class NotifierConfig:
    def __init__(
        self,
        type: str = "discord",
        webhook_url: Optional[str] = None,
        ntfy_url: str = "https://ntfy.sh",
        ntfy_topic: Optional[str] = None,
        telegram_bot_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_ping: str = "",
    ):
        self.type = type
        self.webhook_url = webhook_url
        self.ntfy_url = ntfy_url
        self.ntfy_topic = ntfy_topic
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.discord_ping = discord_ping


class PreferencesConfig:
    def __init__(
        self,
        liked_categories: Optional[List[str]] = None,
        disliked_categories: Optional[List[str]] = None,
        liked_sources: Optional[List[str]] = None,
        disliked_sources: Optional[List[str]] = None,
    ):
        self.liked_categories = liked_categories or []
        self.disliked_categories = disliked_categories or []
        self.liked_sources = liked_sources or []
        self.disliked_sources = disliked_sources or []


class Config:
    def __init__(
        self,
        ai: Optional[AIConfig] = None,
        sources: Optional[List[SourceConfig]] = None,
        schedule: Optional[ScheduleConfig] = None,
        notifier: Optional[NotifierConfig] = None,
        preferences: Optional[PreferencesConfig] = None,
        categories: Optional[List[str]] = None,
    ):
        self.ai = ai or AIConfig()
        self.sources = sources or []
        self.schedule = schedule or ScheduleConfig()
        self.notifier = notifier or NotifierConfig()
        self.preferences = preferences or PreferencesConfig()
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

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        config_file = Path(config_path)
        if not config_file.exists():
            config = cls()
            config.save(config_path)
            return config

        with open(config_file, "r") as f:
            data = yaml.safe_load(f) or {}

        ai_data = data.get("ai", {})
        ai_config = AIConfig(**ai_data) if ai_data else AIConfig()

        sources_data = data.get("sources", [])
        sources = [SourceConfig(**s) for s in sources_data]

        schedule_data = data.get("schedule", {})
        schedule_config = ScheduleConfig(**schedule_data) if schedule_data else ScheduleConfig()

        notifier_data = data.get("notifier", {})
        notifier_config = NotifierConfig(**notifier_data) if notifier_data else NotifierConfig()

        prefs_data = data.get("preferences", {})
        preferences_config = PreferencesConfig(**prefs_data) if prefs_data else PreferencesConfig()

        categories = data.get("categories")

        return cls(ai_config, sources, schedule_config, notifier_config, preferences_config, categories)

    def save(self, config_path: str = "config.yaml") -> None:
        config_dict = {
            "ai": {
                "provider": self.ai.provider,
                "base_url": self.ai.base_url,
                "model": self.ai.model,
                "api_key": self.ai.api_key,
            },
            "sources": [
                {"type": s.type, "name": s.name, "url": s.url, "max_articles": s.max_articles}
                for s in self.sources
            ],
            "schedule": {
                "time": self.schedule.time,
                "timezone": self.schedule.timezone,
                "max_articles": self.schedule.max_articles,
            },
            "notifier": {
                "type": self.notifier.type,
                "webhook_url": self.notifier.webhook_url,
                "ntfy_url": self.notifier.ntfy_url,
                "ntfy_topic": self.notifier.ntfy_topic,
                "telegram_bot_token": self.notifier.telegram_bot_token,
                "telegram_chat_id": self.notifier.telegram_chat_id,
                "discord_ping": self.notifier.discord_ping,
            },
            "categories": self.categories,
            "preferences": {
                "liked_categories": self.preferences.liked_categories,
                "disliked_categories": self.preferences.disliked_categories,
                "liked_sources": self.preferences.liked_sources,
                "disliked_sources": self.preferences.disliked_sources,
            },
        }
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
