import asyncio
import threading

import click

from src.config import Config
from src.scheduler.runner import DigestRunner
from src.scheduler.scheduler import DigestScheduler
from src.storage.json_store import JSONStore


@click.group()
def cli():
    """Clippings - AI-powered daily news digest."""
    pass


@cli.command()
def init():
    """Interactive configuration wizard."""
    click.echo("=== Clippings Configuration ===\n")

    click.echo("AI Backend:")
    provider = click.prompt(
        "  Provider (ollama/openai/anthropic/openai-compatible)",
        default="ollama",
    )
    base_url = click.prompt("  Base URL", default="http://localhost:11434")
    model = click.prompt("  Model", default="llama3.1")
    api_key = click.prompt("  API Key (leave empty for local)", default="", hide_input=True)

    click.echo("\nSources:")
    sources = []
    while True:
        source_type = click.prompt(
            "  Add source type (rss/hackernews/bbc, or 'done')",
            default="done" if sources else "hackernews",
        )
        if source_type == "done" and sources:
            break

        name = click.prompt("  Source name", default=f"{source_type.title()} Feed")
        max_articles = click.prompt("  Max articles", default=10, type=int)

        if source_type == "rss":
            url = click.prompt("  RSS feed URL")
            sources.append(
                {
                    "type": source_type,
                    "name": name,
                    "url": url,
                    "max_articles": max_articles,
                }
            )
        else:
            sources.append(
                {
                    "type": source_type,
                    "name": name,
                    "url": None,
                    "max_articles": max_articles,
                }
            )

    click.echo("\nSchedule:")
    time = click.prompt("  Digest time (HH:MM)", default="08:00")
    timezone = click.prompt("  Timezone", default="UTC")

    click.echo("\nNotifications:")
    notifier_type = click.prompt("  Notifier (discord/ntfy/telegram)", default="discord")

    webhook_url = None
    ntfy_url = "https://ntfy.sh"
    ntfy_topic = None
    telegram_bot_token = None
    telegram_chat_id = None

    if notifier_type == "discord":
        webhook_url = click.prompt("  Discord webhook URL")
    elif notifier_type == "ntfy":
        ntfy_topic = click.prompt("  ntfy topic")
    elif notifier_type == "telegram":
        telegram_bot_token = click.prompt("  Telegram bot token")
        telegram_chat_id = click.prompt("  Telegram chat ID")

    config = Config()
    config.ai.provider = provider
    config.ai.base_url = base_url
    config.ai.model = model
    config.ai.api_key = api_key
    config.sources = []
    for s in sources:
        from src.config import SourceConfig

        config.sources.append(SourceConfig(**s))
    config.schedule.time = time
    config.schedule.timezone = timezone
    config.notifier.type = notifier_type
    config.notifier.webhook_url = webhook_url
    config.notifier.ntfy_url = ntfy_url
    config.notifier.ntfy_topic = ntfy_topic
    config.notifier.telegram_bot_token = telegram_bot_token
    config.notifier.telegram_chat_id = telegram_chat_id

    config.save()
    click.echo("\nConfiguration saved to config.yaml")


@cli.command()
def run():
    """Run the digest pipeline immediately."""
    click.echo("Running digest pipeline...")
    config = Config.load()
    runner = DigestRunner(config)
    asyncio.run(runner.run())
    click.echo("Digest complete!")


@cli.command()
def resend():
    """Resend the last cached digest (skips fetch/summarize)."""
    config = Config.load()
    runner = DigestRunner(config)
    asyncio.run(runner.run(use_cache=True))


@cli.command()
def status():
    """Show the next scheduled digest run."""
    config = Config.load()
    scheduler = DigestScheduler(config)
    scheduler.setup()
    next_run = scheduler.get_next_run()
    click.echo(f"Next digest scheduled at: {next_run}")
    click.echo(f"Sources: {len(config.sources)}")
    click.echo(f"Notifier: {config.notifier.type}")
    click.echo(f"AI: {config.ai.provider}/{config.ai.model}")


@cli.command()
def preferences():
    """View learned preferences."""
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

    click.echo("=== Learned Preferences ===\n")
    liked_cats = prefs.get("liked_categories", []) or ["none"]
    disliked_cats = prefs.get("disliked_categories", []) or ["none"]
    liked_srcs = prefs.get("liked_sources", []) or ["none"]
    disliked_srcs = prefs.get("disliked_sources", []) or ["none"]
    click.echo(f"Liked categories: {', '.join(liked_cats)}")
    click.echo(f"Disliked categories: {', '.join(disliked_cats)}")
    click.echo(f"Liked sources: {', '.join(liked_srcs)}")
    click.echo(f"Disliked sources: {', '.join(disliked_srcs)}")

    feedback = prefs.get("article_feedback", [])
    click.echo(f"\nTotal feedback entries: {len(feedback)}")

    if feedback:
        click.echo("\nRecent feedback:")
        for entry in feedback[-10:]:
            cat = entry.get("category", "")
            cat_str = f" [{cat}]" if cat else ""
            click.echo(f"  {entry['action'].upper()} - {entry['source']}{cat_str}")


@cli.command()
@click.option("--host", default="0.0.0.0", help="Web UI host")
@click.option("--port", default=8000, type=int, help="Web UI port")
def serve(host, port):
    """Start the scheduler and web UI."""
    config = Config.load()
    click.echo("Starting Clippings...")
    click.echo(f"  Sources: {len(config.sources)}")
    click.echo(f"  Notifier: {config.notifier.type}")
    click.echo(f"  AI: {config.ai.provider}/{config.ai.model}")
    click.echo(f"  Schedule: {config.schedule.time} {config.schedule.timezone}")
    click.echo(f"  Web UI: http://{host}:{port}")
    click.echo("")

    def start_scheduler():
        scheduler = DigestScheduler(config)
        scheduler.start()

    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()

    import uvicorn

    uvicorn.run("src.web.app:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    cli()
