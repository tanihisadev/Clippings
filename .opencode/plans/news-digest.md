# News Digest - Implementation Plan

## Overview
A self-hosted, AI-powered daily news digest that aggregates articles from configurable sources, summarizes them, groups by topic, and delivers them to your preferred notification channel. Learns preferences through like/dislike feedback.

## Architecture

```
digest/
├── config.yaml                 # User configuration
├── data/                       # JSON storage (auto-created)
│   ├── preferences.json        # Learned preferences
│   └── history.json            # Digest run history
├── src/
│   ├── main.py                 # CLI entry point (click)
│   ├── config.py               # Config loading/validation (YAML)
│   ├── fetcher/                # News source fetchers
│   │   ├── base.py             # Abstract fetcher interface
│   │   ├── models.py           # Article dataclass
│   │   ├── rss.py              # Generic RSS fetcher (feedparser)
│   │   ├── hackernews.py       # HN API fetcher (httpx)
│   │   └── bbc.py              # BBC News (RSS-based)
│   ├── summarizer/
│   │   └── ai.py               # LiteLLM article summarizer
│   ├── grouper/
│   │   └── topic.py            # AI-powered topic grouping
│   ├── notifier/               # Notification channels
│   │   ├── base.py             # Abstract notifier interface
│   │   ├── discord.py          # Discord webhook
│   │   ├── ntfy.py             # ntfy.sh
│   │   └── telegram.py         # Telegram Bot API
│   ├── scheduler/
│   │   ├── runner.py           # Digest pipeline orchestrator
│   │   └── scheduler.py        # APScheduler daily cron
│   └── storage/
│       └── json_store.py       # Thread-safe JSON storage
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Pipeline Flow
1. Scheduler triggers at configured time (or user runs `digest run`)
2. Fetchers pull articles from all configured sources
3. Articles are deduplicated by URL
4. Articles scored against user preferences
5. AI summarizes each article (LiteLLM)
6. AI groups articles by topic (LiteLLM)
7. Articles grouped by topic → source
8. Formatted digest sent via chosen notifier
9. Digest recorded in history
10. User interacts with like/dislike → preferences updated

## AI Backend Support
- Ollama (default): `base_url: http://localhost:11434`
- llama.cpp server: `base_url: http://localhost:8080/v1`
- OpenAI: `provider: openai`, `api_key: sk-...`
- Any OpenAI-compatible API

## CLI Commands
- `digest init` - Interactive config wizard
- `digest run` - Run digest immediately
- `digest status` - Show next scheduled run
- `digest preferences` - View learned preferences
- `digest serve` - Start scheduler
