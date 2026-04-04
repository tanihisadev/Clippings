from abc import ABC, abstractmethod
from typing import Dict, List
from src.fetcher.models import Article


class BaseNotifier(ABC):
    """Abstract base class for notification channels."""

    @abstractmethod
    async def send(self, groups: Dict[str, Dict[str, List[Article]]]) -> str:
        """Send the digest. Returns message ID for tracking reactions."""
        pass
