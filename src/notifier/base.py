from abc import ABC, abstractmethod

from src.fetcher.models import Article


class BaseNotifier(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, groups: dict[str, dict[str, list[Article]]]) -> str:
        """Send the digest. Returns message ID for tracking reactions."""
        pass
