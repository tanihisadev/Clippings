import json
import re
import shutil
import tempfile
import threading
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

STOPWORDS = frozenset(
    "a an the is it in on at to for of and or but not with from by "
    "this that these those has have had was were are be been being "
    "do does did will would can could should may might shall "
    "about after before between during into through under over "
    "again further then once here there when where why how all "
    "both each every other some such no nor only own same so "
    "than too very also back even still way look many make "
    "get go see now long just know take come make like want "
    "use new give day way well down his her its our his they "
    "she him say says said one two three four five six seven eight nine ten"
    .split()
)


def extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text, removing stopwords and punctuation."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    words = [w for w in text.split() if len(w) > 2 and w not in STOPWORDS]
    return words


class JSONStore:
    """Thread-safe JSON file storage for preferences and history."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _file_path(self, name: str) -> Path:
        return self.data_dir / f"{name}.json"

    def load(self, name: str, default: Any = None) -> Any:
        path = self._file_path(name)
        if not path.exists():
            return default if default is not None else {}
        with open(path) as f:
            return json.load(f)

    def save(self, name: str, data: Any) -> None:
        with self._lock:
            path = self._file_path(name)
            fd, tmp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")
            try:
                with open(fd, "w") as f:
                    json.dump(data, f, indent=2, default=str)
                shutil.move(tmp_path, path)
            except Exception:
                try:
                    Path(tmp_path).unlink()
                except OSError:
                    pass
                raise

    def update_preferences(
        self,
        article_id: str,
        action: str,
        source: str,
        category: str = "",
        article_text: str = "",
    ) -> None:
        prefs = self.load(
            "preferences",
            {
                "liked_keywords": {},
                "disliked_keywords": {},
                "article_feedback": [],
            },
        )

        keywords = extract_keywords(article_text)
        freq = Counter(keywords)

        feedback_entry = {
            "article_id": article_id,
            "action": action,
            "source": source,
            "category": category,
            "keywords": keywords,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if "article_feedback" not in prefs:
            prefs["article_feedback"] = []
        prefs["article_feedback"].append(feedback_entry)

        if "liked_keywords" not in prefs:
            prefs["liked_keywords"] = {}
        if "disliked_keywords" not in prefs:
            prefs["disliked_keywords"] = {}

        pool_key = "liked_keywords" if action == "like" else "disliked_keywords"
        pool = prefs[pool_key]
        for word, count in freq.items():
            pool[word] = pool.get(word, 0) + count

        self.save("preferences", prefs)

    def record_digest(self, articles_count: int, sources: list[str], message_id: str) -> None:
        history = self.load("history", {"digests": []})
        if "digests" not in history:
            history["digests"] = []

        history["digests"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "articles_count": articles_count,
                "sources": sources,
                "message_id": message_id,
            }
        )

        self.save("history", history)

    def score_article(self, title: str, summary: str = "", source: str = "") -> float:
        """Score an article based on keyword overlap with liked/disliked pools."""
        prefs = self.load("preferences", {"liked_keywords": {}, "disliked_keywords": {}})
        liked = prefs.get("liked_keywords", {})
        disliked = prefs.get("disliked_keywords", {})

        if not liked and not disliked:
            return 0.0

        text = f"{title} {summary}".lower()
        text = re.sub(r"[^\w\s]", "", text)
        words = set(text.split())
        words = {w for w in words if len(w) > 2 and w not in STOPWORDS}

        liked_hits = sum(liked.get(w, 0) for w in words)
        disliked_hits = sum(disliked.get(w, 0) for w in words)

        return liked_hits - disliked_hits

    def get_top_keywords(self, pool_key: str = "liked_keywords", limit: int = 15) -> list[str]:
        """Get the top keywords from a preference pool."""
        prefs = self.load("preferences", {"liked_keywords": {}, "disliked_keywords": {}})
        pool = prefs.get(pool_key, {})
        sorted_kw = sorted(pool.items(), key=lambda x: x[1], reverse=True)
        return [kw for kw, _ in sorted_kw[:limit]]

    def reset_preferences(self) -> None:
        """Reset all learned keyword preferences."""
        self.save(
            "preferences",
            {
                "liked_keywords": {},
                "disliked_keywords": {},
                "article_feedback": [],
            },
        )
