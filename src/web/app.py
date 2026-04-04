import asyncio
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from src.config import Config
from src.scheduler.runner import DigestRunner
from src.scheduler.scheduler import DigestScheduler
from src.storage.json_store import JSONStore

app = FastAPI(title="Clippings", docs_url="/api/docs")

CONFIG_PATH = "config.yaml"

_run_status = {"running": False, "log": [], "started_at": None}


class LogCapture:
    def __init__(self):
        self.log = []

    def write(self, text):
        self.log.append(text.strip())
        _run_status["log"] = self.log[-50:]

    def flush(self):
        pass


def _run_digest_sync():
    _run_status["running"] = True
    _run_status["log"] = []
    _run_status["started_at"] = datetime.now(UTC).isoformat()

    capture = LogCapture()
    old_stdout = sys.stdout
    sys.stdout = capture

    try:
        config = Config.load(CONFIG_PATH)
        runner = DigestRunner(config)
        asyncio.run(runner.run())
    except Exception as e:
        capture.write(f"Error: {e}")
    finally:
        sys.stdout = old_stdout
        _run_status["running"] = False


@app.get("/", response_class=HTMLResponse)
async def index():
    html = Path("src/web/index.html").read_text()
    return html


@app.get("/api/config")
async def get_config():
    config = Config.load(CONFIG_PATH)
    return {
        "ai": {
            "provider": config.ai.provider,
            "base_url": config.ai.base_url,
            "model": config.ai.model,
            "api_key": config.ai.api_key,
        },
        "sources": [
            {"type": s.type, "name": s.name, "url": s.url, "max_articles": s.max_articles}
            for s in config.sources
        ],
        "schedule": {
            "time": config.schedule.time,
            "timezone": config.schedule.timezone,
            "max_articles": config.schedule.max_articles,
        },
        "notifier": {
            "type": config.notifier.type,
            "webhook_url": config.notifier.webhook_url,
            "discord_ping": config.notifier.discord_ping,
            "ntfy_url": config.notifier.ntfy_url,
            "ntfy_topic": config.notifier.ntfy_topic,
            "telegram_bot_token": config.notifier.telegram_bot_token,
            "telegram_chat_id": config.notifier.telegram_chat_id,
        },
        "categories": config.categories,
        "preferences": {
            "liked_categories": config.preferences.liked_categories,
            "disliked_categories": config.preferences.disliked_categories,
            "liked_sources": config.preferences.liked_sources,
            "disliked_sources": config.preferences.disliked_sources,
        },
    }


@app.post("/api/config")
async def save_config(data: dict):
    try:
        config = Config()
        config.ai.provider = data["ai"]["provider"]
        config.ai.base_url = data["ai"]["base_url"]
        config.ai.model = data["ai"]["model"]
        config.ai.api_key = data["ai"].get("api_key", "")

        from src.config import SourceConfig

        config.sources = [SourceConfig(**s) for s in data.get("sources", [])]
        config.schedule.time = data["schedule"].get("time", "08:00")
        config.schedule.timezone = data["schedule"].get("timezone", "UTC")
        config.schedule.max_articles = data["schedule"].get("max_articles", 20)

        config.notifier.type = data["notifier"].get("type", "discord")
        config.notifier.webhook_url = data["notifier"].get("webhook_url")
        config.notifier.discord_ping = data["notifier"].get("discord_ping", "")
        config.notifier.ntfy_url = data["notifier"].get("ntfy_url", "https://ntfy.sh")
        config.notifier.ntfy_topic = data["notifier"].get("ntfy_topic")
        config.notifier.telegram_bot_token = data["notifier"].get("telegram_bot_token")
        config.notifier.telegram_chat_id = data["notifier"].get("telegram_chat_id")

        config.categories = data.get("categories", [])
        prefs = data.get("preferences", {})
        config.preferences.liked_categories = prefs.get("liked_categories", [])
        config.preferences.disliked_categories = prefs.get("disliked_categories", [])
        config.preferences.liked_sources = prefs.get("liked_sources", [])
        config.preferences.disliked_sources = prefs.get("disliked_sources", [])

        config.save(CONFIG_PATH)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/run")
async def trigger_run():
    if _run_status["running"]:
        raise HTTPException(status_code=409, detail="Digest already running")
    t = threading.Thread(target=_run_digest_sync, daemon=True)
    t.start()
    return {"status": "ok"}


@app.get("/api/run-status")
async def run_status():
    return _run_status


@app.get("/api/status")
async def get_status():
    config = Config.load(CONFIG_PATH)
    scheduler = DigestScheduler(config)
    scheduler.setup()
    return {
        "next_run": scheduler.get_next_run(),
        "sources": len(config.sources),
        "notifier": config.notifier.type,
        "ai_provider": config.ai.provider,
        "ai_model": config.ai.model,
    }


@app.get("/api/preferences")
async def get_preferences():
    store = JSONStore()
    prefs = store.load(
        "preferences",
        {
            "liked_categories": [],
            "disliked_categories": [],
            "liked_sources": [],
            "disliked_sources": [],
            "article_feedback": [],
        },
    )
    return prefs


@app.post("/api/preferences")
async def update_preferences(data: dict):
    store = JSONStore()
    store.save("preferences", data)
    return {"status": "ok"}
