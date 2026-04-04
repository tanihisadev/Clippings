import asyncio
import threading

import discord
from discord.ext import commands

from src.fetcher.models import Article
from src.notifier.base import BaseNotifier
from src.storage.json_store import JSONStore

_bot = None
_ready_event = threading.Event()
_sent_messages = []
_store = JSONStore()
_bot_loop = None


def get_bot():
    global _bot
    return _bot


def _run_coro(coro):
    """Run a coroutine on the bot's event loop from another thread."""
    future = asyncio.run_coroutine_threadsafe(coro, _bot_loop)
    return future.result(timeout=120)


def start_discord_bot(token: str) -> None:
    global _bot, _bot_loop

    if _bot is not None:
        return

    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    _bot = commands.Bot(command_prefix="!", intents=intents)

    @_bot.event
    async def on_ready():
        global _bot_loop
        _bot_loop = asyncio.get_event_loop()
        _ready_event.set()
        print(f"Discord bot ready as {_bot.user}")

    @_bot.event
    async def on_raw_reaction_add(payload):
        if payload.user_id == _bot.user.id:
            return
        if payload.emoji.name not in ("\U0001f44d", "\U0001f44e"):
            return

        for msg_info in _sent_messages:
            if msg_info["message_id"] == payload.message_id:
                action = "like" if payload.emoji.name == "\U0001f44d" else "dislike"
                _store.update_preferences(
                    article_id=msg_info["article_id"],
                    action=action,
                    source=msg_info["source"],
                    category=msg_info["category"],
                )
                print(f"  Feedback: {action} -> {msg_info['category']}/{msg_info['source']}")
                break

    def run():
        _bot.run(token)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    _ready_event.wait(timeout=15)


class DiscordNotifier(BaseNotifier):
    """Send digest via Discord bot with per-article reactions."""

    def __init__(self, bot_token: str, channel_id: int, ping: str = ""):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.ping = ping

    async def send(self, groups: dict[str, dict[str, list[Article]]]) -> str:
        global _sent_messages
        _sent_messages = []

        if _bot is None:
            start_discord_bot(self.bot_token)

        async def _do_send():
            global _sent_messages

            cid = self.channel_id
            print(f"  Discord: sending to channel_id={cid} (type={type(cid).__name__})")
            channel = _bot.get_channel(cid)
            print(f"  Discord: get_channel returned {channel}")
            if not channel:
                print("  Discord: fetching channel...")
                channel = await _bot.fetch_channel(cid)
                print(f"  Discord: fetch_channel returned {channel}")

            ping_msg = None
            if self.ping == "everyone":
                ping_msg = (
                    "@everyone **Clippings** \u2014 "
                    "react \U0001f44d/\U0001f44e to train preferences"
                )
            elif self.ping == "here":
                ping_msg = (
                    "@here **Clippings** \u2014 react \U0001f44d/\U0001f44e to train preferences"
                )
            elif self.ping:
                ping_msg = (
                    f"{self.ping} **Clippings** \u2014 "
                    "react \U0001f44d/\U0001f44e to train preferences"
                )
            if ping_msg:
                await channel.send(ping_msg)

            for category, sources in groups.items():
                await channel.send(f"\n# ---{category}---")

                for source_name, articles in sources.items():
                    for article in articles:
                        summary = article.summary or ""
                        if len(summary) > 120:
                            summary = summary[:117] + "..."

                        content = f"**{article.title}**"
                        if summary:
                            content += f"\n{summary}"
                        content += f"\n{article.url}"

                        msg = await channel.send(content)
                        await msg.add_reaction("\U0001f44d")
                        await msg.add_reaction("\U0001f44e")

                        _sent_messages.append(
                            {
                                "message_id": msg.id,
                                "category": category,
                                "source": source_name,
                                "article_id": article.id,
                            }
                        )

        _run_coro(_do_send())
        return "discord"
