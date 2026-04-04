import os

import discord
from discord.ext import commands

from src.config import Config
from src.storage.json_store import JSONStore

store = JSONStore()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

_CHANNEL = None
_GROUPS = {}
_SENT_MESSAGES = []


@bot.event
async def on_ready():
    print(f"Discord bot ready as {bot.user}")


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    if payload.emoji.name not in ("👍", "👎"):
        return

    for msg_info in _SENT_MESSAGES:
        if msg_info["message_id"] == payload.message_id:
            action = "like" if payload.emoji.name == "👍" else "dislike"
            category = msg_info["category"]
            source = msg_info["source"]
            article_id = msg_info["article_id"]
            store.update_preferences(
                article_id=article_id,
                action=action,
                source=source,
                category=category,
            )
            print(f"  Feedback: {action} -> {category}/{source}")
            break


async def send_digest(groups: dict, channel_id: int, ping: str = "") -> str:
    channel = bot.get_channel(channel_id)
    if not channel:
        channel = await bot.fetch_channel(channel_id)

    _SENT_MESSAGES.clear()

    if ping == "everyone":
        await channel.send("@everyone **Clippings** — react 👍/👎 on each article to train preferences")
    elif ping == "here":
        await channel.send("@here **Clippings** — react 👍/👎 on each article to train preferences")
    elif ping:
        await channel.send(f"{ping} **Clippings** — react 👍/👎 on each article to train preferences")

    for category, sources in groups.items():
        for source_name, articles in sources.items():
            for article in articles:
                lines = []
                if article.summary:
                    lines.append(f"_ {article.summary}")
                lines.append(f"[{article.title}]({article.url})")
                content = "\n".join(lines)

                msg = await channel.send(content)
                await msg.add_reaction("👍")
                await msg.add_reaction("👎")

                _SENT_MESSAGES.append({
                    "message_id": msg.id,
                    "category": category,
                    "source": source_name,
                    "article_id": article.id,
                })

    return "discord"


def run_bot(token: str):
    bot.run(token)
