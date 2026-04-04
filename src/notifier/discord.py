import threading

import discord
from discord.ext import commands

from src.fetcher.models import Article
from src.notifier.base import BaseNotifier
from src.storage.json_store import JSONStore

_intents = discord.Intents.default()
_intents.message_content = True
_intents.reactions = True

_bot = commands.Bot(command_prefix="!", intents=_intents)
_store = JSONStore()
_sent_messages = []
_ready_event = threading.Event()


@_bot.event
async def on_ready():
    _ready_event.set()


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


class DiscordNotifier(BaseNotifier):
    """Send digest via Discord bot with per-article reactions."""

    def __init__(self, bot_token: str, channel_id: int, ping: str = ""):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.ping = ping

    async def send(self, groups: dict[str, dict[str, list[Article]]]) -> str:
        _sent_messages.clear()
        _ready_event.clear()

        def start_bot():
            _bot.run(self.bot_token)

        thread = threading.Thread(target=start_bot, daemon=True)
        thread.start()

        _ready_event.wait(timeout=15)

        channel = _bot.get_channel(self.channel_id)
        if not channel:
            channel = await _bot.fetch_channel(self.channel_id)

        if self.ping == "everyone":
            await channel.send(
                "@everyone **Clippings** — react \U0001f44d/\U0001f44e on each article to train preferences"
            )
        elif self.ping == "here":
            await channel.send(
                "@here **Clippings** — react \U0001f44d/\U0001f44e on each article to train preferences"
            )
        elif self.ping:
            await channel.send(
                f"{self.ping} **Clippings** — react \U0001f44d/\U0001f44e on each article to train preferences"
            )

        for category, sources in groups.items():
            for source_name, articles in sources.items():
                for article in articles:
                    lines = []
                    if article.summary:
                        lines.append(f"_ {article.summary}")
                    lines.append(f"[{article.title}]({article.url})")
                    content = "\n".join(lines)

                    msg = await channel.send(content)
                    await msg.add_reaction("\U0001f44d")
                    await msg.add_reaction("\U0001f44e")

                    _sent_messages.append({
                        "message_id": msg.id,
                        "category": category,
                        "source": source_name,
                        "article_id": article.id,
                    })

        return "discord"
