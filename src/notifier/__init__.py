from src.notifier.discord import DiscordNotifier
from src.notifier.ntfy import NtfyNotifier
from src.notifier.telegram import TelegramNotifier
from src.notifier.base import BaseNotifier

NOTIFIER_MAP = {
    "discord": DiscordNotifier,
    "ntfy": NtfyNotifier,
    "telegram": TelegramNotifier,
}


def get_notifier(notifier_type: str, **kwargs) -> BaseNotifier:
    """Factory function to get the appropriate notifier."""
    notifier_cls = NOTIFIER_MAP.get(notifier_type)
    if not notifier_cls:
        raise ValueError(f"Unknown notifier type: {notifier_type}. Available: {list(NOTIFIER_MAP.keys())}")
    return notifier_cls(**kwargs)
