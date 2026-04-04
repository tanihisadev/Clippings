# Clippings

A self-hosted, AI-powered daily news digest that aggregates articles from configurable sources, summarizes them, groups by topic, and delivers them to your preferred notification channel. Over time, it learns your preferences through like/dislike feedback.

## Features

- **Configurable sources** — RSS feeds, Hacker News, BBC News, and more
- **AI-powered summaries** — Every article summarized by an LLM
- **Topic grouping** — Articles grouped into categories by AI
- **Preference learning** — Like/dislike articles to train your feed
- **Multiple AI backends** — Ollama, llama.cpp, OpenAI, Anthropic, or any OpenAI-compatible API
- **Multiple notification channels** — Discord, ntfy.sh, or Telegram
- **Self-hosted** — Runs locally or in Docker, zero cloud dependency

## Quick Start

### 1. Install

```bash
# Clone the repo
git clone https://github.com/yourusername/clippings.git
cd clippings

# Install dependencies
pip install .
```

### 2. Configure

Run the interactive setup wizard:

```bash
digest init
```

Or edit `config.yaml` directly (see [Configuration](#configuration) below).

### 3. Run

```bash
# Run a digest immediately
digest run

# Start the daily scheduler
digest serve
```

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
  - type: bbc
    name: BBC Tech
    url: http://feeds.bbci.co.uk/news/technology/rss.xml
    max_articles: 10

schedule:
  time: "08:00"                       # 24h format
  timezone: UTC                       # Any valid timezone

notifier:
  type: discord                       # discord, ntfy, telegram
  webhook_url: "https://discord.com/api/webhooks/..."
  ntfy_url: "https://ntfy.sh"
  ntfy_topic: "my-digest"
  telegram_bot_token: ""
  telegram_chat_id: ""

preferences:
  liked_topics: []                    # Auto-populated over time
  disliked_topics: []
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

1. Run llama.cpp with its OpenAI-compatible server:
   ```bash
   ./llama-server -m your-model.gguf --port 8080
   ```
2. Configure:
   ```yaml
   ai:
     provider: openai-compatible
     base_url: http://localhost:8080/v1
     model: your-model
   ```

### Cloud Providers (OpenAI, Anthropic, etc.)

```yaml
ai:
  provider: openai
  base_url: ""                        # Leave empty for default
  model: gpt-4o
  api_key: "sk-..."
```

## Notification Setup

### Discord

1. Go to your Discord channel → Edit Channel → Integrations → Webhooks
2. Create a webhook and copy the URL
3. Set in config:
   ```yaml
   notifier:
     type: discord
     webhook_url: "https://discord.com/api/webhooks/..."
   ```

### ntfy.sh

1. Choose a topic name (e.g., `my-news-digest`)
2. Set in config:
   ```yaml
   notifier:
     type: ntfy
     ntfy_url: "https://ntfy.sh"      # Or your self-hosted instance
     ntfy_topic: "my-news-digest"
   ```

### Telegram

1. Create a bot via [@BotFather](https://t.me/BotFather) and get the token
2. Get your chat ID (send a message to [@userinfobot](https://t.me/userinfobot))
3. Set in config:
   ```yaml
   notifier:
     type: telegram
     telegram_bot_token: "123456:ABC-..."
     telegram_chat_id: "123456789"
   ```

## Adding Custom RSS Sources

Add any RSS feed to the `sources` list:

```yaml
sources:
  - type: rss
    name: Ars Technica
    url: https://arstechnica.com/feed/
    max_articles: 10
  - type: rss
    name: The Verge
    url: https://www.theverge.com/rss/index.xml
    max_articles: 10
```

## How Preference Learning Works

Feedback is tracked at the **source level** (e.g., "hackernews", "BBC News"), not by topic name. This is because the AI generates different topic labels each run ("Technology & AI" vs "Tech" vs "Software"), making topic-based tracking unreliable.

1. Each digest message includes like/dislike options (emoji reactions on Discord, action buttons on ntfy, inline keyboard on Telegram)
2. When you interact, the feedback is saved to `data/preferences.json` with the article's source
3. After 2+ likes or dislikes from the same source, it's added to your liked/disliked sources list
4. Future digests score articles against your preferences — liked sources are boosted, disliked ones are demoted
5. View your learned preferences anytime with `digest preferences`

## Docker Deployment

```bash
# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Run a digest manually
docker compose exec digest digest run
```

Mount your own config and data:

```yaml
volumes:
  - ./config.yaml:/app/config.yaml:ro
  - ./data:/app/data
```

If using a local AI backend (Ollama/llama.cpp), make sure the container can reach it. You may need to set `base_url` to your host machine's IP or use `network_mode: host`.

## Deploying on Proxmox

### Option 1: LXC + Docker (Recommended)

This runs digest in an isolated container alongside your other services.

**Step 1: Create the LXC**

In the Proxmox web UI:
1. Create CT → Template: Debian 12
2. Resources: 2 cores, 4GB RAM, 10GB disk
3. Network: bridge (vmbr0), DHCP or static IP
4. Options: Uncheck "Unprivileged container" (easier for Docker)

**Step 2: Install Docker**

SSH into the LXC:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER
```

**Step 3: Deploy digest**

```bash
# Clone the repo
git clone https://github.com/yourusername/clippings.git
cd clippings

# Copy and edit config
cp config.example.yaml config.yaml
nano config.yaml
```

Point `base_url` to your Proxmox host's IP (where Ollama/llama.cpp runs):

```yaml
ai:
  base_url: http://192.168.1.100:11434   # Your Proxmox host IP
  model: llama3.1
```

```bash
# Start
docker compose up -d
```

### Option 2: Direct on Proxmox Host

Skip the LXC entirely and run directly on the Proxmox host alongside Ollama/llama.cpp:

```bash
# On the Proxmox host
apt install python3 python3-pip python3-venv
git clone https://github.com/yourusername/clippings.git
cd clippings

python3 -m venv .venv
source .venv/bin/activate
pip install -e .

cp config.example.yaml config.yaml
nano config.yaml  # set base_url to http://localhost:11434

# Run as a systemd service
cat > /etc/systemd/system/clippings.service << 'EOF'
[Unit]
Description=Clippings Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/clippings
ExecStart=/root/clippings/.venv/bin/digest serve
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now clippings
```

### Architecture

```
┌──────────────────────────────────────────────────────┐
│  Proxmox Host                                        │
│                                                      │
│  ┌─────────────────┐    ┌────────────────────────┐   │
│  │ Ollama /        │    │ LXC (Debian 12)        │   │
│  │ llama.cpp       │◄───┤                        │   │
│  │ :11434          │    │  Docker: clippings       │   │
│  │                 │    │  :8000                 │   │
│  └─────────────────┘    └────────────────────────┘   │
│                                                      │
│  Or run digest directly on host (no LXC needed)      │
└──────────────────────────────────────────────────────┘
```

## Local Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check .

# Run tests
pytest
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `digest init` | Interactive configuration wizard |
| `digest run` | Run the digest pipeline immediately |
| `digest resend` | Resend last cached digest (skips fetch/summarize) |
| `digest status` | Show next scheduled run and config summary |
| `digest preferences` | View learned preferences and feedback history |
| `digest serve` | Start the daily scheduler |

## Project Structure

```
digest/
├── config.yaml                 # User configuration
├── data/                       # JSON storage (auto-created)
│   ├── preferences.json        # Learned preferences
│   └── history.json            # Digest run history
├── src/
│   ├── main.py                 # CLI entry point
│   ├── config.py               # Config loading/validation
│   ├── fetcher/                # News source fetchers
│   │   ├── base.py             # Abstract fetcher interface
│   │   ├── rss.py              # Generic RSS fetcher
│   │   ├── hackernews.py       # HN API fetcher
│   │   └── bbc.py              # BBC News fetcher
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

## License

MIT
