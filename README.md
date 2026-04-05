# Clippings

A self-hosted, AI-powered daily news digest that aggregates articles from configurable sources, summarizes them, groups by topic, and delivers them to your preferred notification channel. Over time, it learns your preferences through like/dislike feedback.

## Features

- **Configurable sources** — RSS feeds, Hacker News, BBC News, and more
- **AI-powered summaries** — Every article summarized by an LLM
- **Fixed categories** — Articles sorted into user-defined categories (Technology, Science, Politics, etc.)
- **Preference learning** — Like/dislike to train your feed
- **Multiple AI backends** — Ollama, llama.cpp, OpenAI, Anthropic, or any OpenAI-compatible API
- **Multiple notification channels** — Discord, ntfy.sh, or Telegram
- **Self-hosted** — Runs anywhere, zero cloud dependency

## Quick Start

### 1. Install

**Docker (recommended):**

```bash
git clone https://github.com/tanihisadev/clippings.git
cd clippings
docker compose up -d
```

Open `http://localhost:3000` in your browser to configure everything.

**Native (pip):**

Requires Python 3.11+, pip, and build tools for compiling dependencies:

```bash
# Debian/Ubuntu
apt install python3 python3-pip python3-venv gcc libxml2-dev libxslt-dev

git clone https://github.com/tanihisadev/clippings.git
cd clippings
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cp config.example.yaml config.yaml
```

Edit `config.yaml`, then run:

```bash
digest run        # run once
digest serve      # start daily scheduler
```

### 2. Configure

See [Configuration](#configuration) below for all options. The quickest way is to edit `config.yaml` directly, or run `digest init` for an interactive wizard (native install only).

### 3. Run

```bash
# Docker
docker compose up -d
# Web UI: http://localhost:3000

# Native
digest run        # run once
digest serve      # start scheduler + web UI on :8000
```

The web UI lets you manage config, sources, categories, and trigger digests from your browser — no SSH needed.

## Configuration

See the detailed guides for each section:

- **[AI Backend](docs/ai-backend.md)** — Ollama, llama.cpp, OpenAI, Anthropic
- **[Sources](docs/sources.md)** — RSS feeds, Hacker News, BBC News
- **[Notifications](docs/notifications.md)** — Discord bot, ntfy.sh, Telegram

### config.yaml (quick reference)

```yaml
ai:
  provider: ollama
  base_url: http://localhost:11434
  model: llama3.1
  api_key: ""

sources:
  - type: hackernews
    name: Hacker News
    max_articles: 10
  - type: rss
    name: BBC News
    url: http://feeds.bbci.co.uk/news/rss.xml
    max_articles: 10

schedule:
  time: "08:00"
  timezone: UTC
  max_articles: 20

notifier:
  type: discord
  discord_bot_token: ""
  discord_channel_id: 0
  discord_ping: "everyone"

categories:
  - Technology
  - Science
  - Politics
  - Business
  - Health
  - Entertainment
  - Sports
  - Other

preferences:
  liked_categories: []
  disliked_categories: []
  liked_sources: []
  disliked_sources: []
```

## How Preference Learning Works

1. Each article is sent as its own message with 👍/👎 reactions
2. Reacting on an article records feedback for that specific category + source
3. After 2+ likes or dislikes from the same source or category, it's added to your preferences
4. Future digests score articles against your preferences — liked sources/categories are boosted, disliked ones are demoted
5. View with `digest preferences`

## Running as a Service

### Docker

```bash
docker compose up -d
```

The container restarts automatically. Config and data persist via volume mounts.

### Native (systemd)

```bash
cat > /etc/systemd/system/clippings.service << 'EOF'
[Unit]
Description=Clippings Scheduler
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/clippings
ExecStart=/path/to/clippings/.venv/bin/digest serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now clippings
```

### Remote AI Backend

If your AI backend runs on a different machine (e.g. separate LXC, another server), set `base_url` to its IP:

```yaml
ai:
  base_url: http://192.168.1.100:11434
  model: llama3.1
```

Both machines must be on the same network.

## CLI Commands

| Command | Description |
|---------|-------------|
| `digest init` | Interactive configuration wizard (CLI) |
| `digest run` | Run the digest pipeline immediately |
| `digest resend` | Resend last cached digest (skips fetch/summarize) |
| `digest status` | Show next scheduled run and config summary |
| `digest preferences` | View learned preferences and feedback history |
| `digest serve` | Start scheduler + web UI on port 8000 |

## Project Structure

```
clippings/
├── config.yaml                 # User configuration
├── config.example.yaml         # Template (safe to commit)
├── data/                       # JSON storage (auto-created)
│   ├── preferences.json        # Learned preferences
│   └── history.json            # Digest run history
├── src/
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Config loading/validation
│   ├── fetcher/                # News source fetchers
│   ├── summarizer/             # AI article summarizer
│   ├── grouper/                # AI topic categorizer
│   ├── notifier/               # Discord, ntfy, Telegram
│   ├── scheduler/              # Pipeline runner + cron
│   └── storage/                # JSON file storage
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Local Development

```bash
pip install -e ".[dev]"
ruff check .
ruff format .
pytest
```

## License

MIT
