PERSONAL PROOF OF CONCEPT PROJECT - WILL REFACTOR LATER.


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
git clone https://github.com/yourusername/clippings.git
cd clippings
docker compose up -d
```

Open `http://localhost:8000` in your browser to configure everything.

**Native (pip):**

Requires Python 3.11+, pip, and build tools for compiling dependencies:

```bash
# Debian/Ubuntu
apt install python3 python3-pip python3-venv gcc libxml2-dev libxslt-dev

git clone https://github.com/yourusername/clippings.git
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
# Web UI: http://localhost:8000

# Native
digest run        # run once
digest serve      # start scheduler + web UI on :8000
```

The web UI at `http://localhost:8000` lets you manage config, sources, categories, and trigger digests from your browser — no SSH needed.

## Configuration

### config.yaml

```yaml
ai:
  provider: ollama                    # ollama, openai, anthropic, openai-compatible
  base_url: http://localhost:11434    # Your AI backend URL
  model: llama3.1                     # Model name
  api_key: ""                         # API key (not needed for local backends)

sources:
  - type: rss
    name: BBC News
    url: http://feeds.bbci.co.uk/news/rss.xml
    max_articles: 10
  - type: hackernews
    max_articles: 15

schedule:
  time: "08:00"                       # 24h format
  timezone: UTC                       # Any valid timezone
  max_articles: 20                    # Max articles in the final digest

notifier:
  type: discord                       # discord, ntfy, telegram
  webhook_url: "https://discord.com/api/webhooks/..."
  discord_ping: "everyone"            # "everyone", "here", "<@USER_ID>", or ""

  # ntfy settings (if type: ntfy)
  ntfy_url: "https://ntfy.sh"
  ntfy_topic: ""

  # telegram settings (if type: telegram)
  telegram_bot_token: ""
  telegram_chat_id: ""

# Fixed categories the AI sorts articles into.
# You can add, remove, or rename these.
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
  # Auto-populated over time via like/dislike feedback
  liked_categories: []
  disliked_categories: []
  liked_sources: []
  disliked_sources: []
```

## AI Backend Setup

### Ollama

1. Install [Ollama](https://ollama.com)
2. Pull a model: `ollama pull llama3.1`
3. Configure:
   ```yaml
   ai:
     provider: ollama
     base_url: http://localhost:11434
     model: llama3.1
   ```

### llama.cpp (Server Mode)

1. Run llama.cpp server:
   ```bash
   ./llama-server -m your-model.gguf --port 8080
   ```
2. Configure:
   ```yaml
   ai:
     provider: openai-compatible
     base_url: http://localhost:8080/v1
     model: default
   ```

### Cloud Providers

```yaml
ai:
  provider: openai
  model: gpt-4o
  api_key: "sk-..."
```

## Notification Setup

### Discord

1. Channel settings → Integrations → Webhooks → Create webhook
2. Copy the URL into your config:
   ```yaml
   notifier:
     type: discord
     webhook_url: "https://discord.com/api/webhooks/..."
     discord_ping: "everyone"
   ```

### ntfy.sh

1. Pick a topic name
2. Configure:
   ```yaml
   notifier:
     type: ntfy
     ntfy_topic: "my-clippings"
   ```

### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
3. Configure:
   ```yaml
   notifier:
     type: telegram
     telegram_bot_token: "123456:ABC-..."
     telegram_chat_id: "123456789"
   ```

## Adding Sources

Add any RSS feed to the `sources` list:

```yaml
sources:
  - type: rss
    name: Ars Technica
    url: https://arstechnica.com/feed/
    max_articles: 10
  - type: hackernews
    max_articles: 15
```

Available source types: `rss`, `hackernews`, `bbc`.

## How Preference Learning Works

1. Each digest includes like/dislike options (emoji reactions on Discord, action buttons on ntfy, inline keyboard on Telegram)
2. Feedback is saved to `data/preferences.json`
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
