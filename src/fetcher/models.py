from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Article:
    id: str
    title: str
    url: str
    source: str
    content: str
    published_at: Optional[datetime] = None
    summary: str = ""
    topic: str = ""
    score: int = 0
    metadata: Dict = field(default_factory=dict)
