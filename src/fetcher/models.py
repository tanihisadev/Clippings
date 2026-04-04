from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    id: str
    title: str
    url: str
    source: str
    content: str
    published_at: datetime | None = None
    summary: str = ""
    topic: str = ""
    score: int = 0
    metadata: dict = field(default_factory=dict)
