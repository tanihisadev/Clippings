import json
import shutil
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


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
    ) -> None:
        prefs = self.load(
            "preferences",
            {
                "liked_categories": [],
                "disliked_categories": [],
                "liked_sources": [],
                "disliked_sources": [],
                "article_feedback": [],
            },
        )

        feedback_entry = {
            "article_id": article_id,
            "action": action,
            "source": source,
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if "article_feedback" not in prefs:
            prefs["article_feedback"] = []
        prefs["article_feedback"].append(feedback_entry)

        self._auto_update_lists(prefs)
        self.save("preferences", prefs)

    def _auto_update_lists(self, prefs: dict) -> None:
        """Auto-populate liked/disliked lists after 2+ feedback entries."""
        feedback = prefs.get("article_feedback", [])

        for field, key in [
            ("liked_categories", "category"),
            ("disliked_categories", "category"),
            ("liked_sources", "source"),
            ("disliked_sources", "source"),
        ]:
            prefix = "like" if "liked" in field else "dislike"
            count = sum(1 for e in feedback if e.get(key) and e["action"] == prefix)
            value = feedback[-1].get(key, "")
            if value and count >= 2 and value not in prefs[field]:
                prefs[field].append(value)

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

    def get_feedback_score(self, source: str, category: str = "") -> int:
        prefs = self.load("preferences", {"article_feedback": []})
        feedback = prefs.get("article_feedback", [])

        score = 0
        for entry in feedback:
            if entry.get("source") == source or (category and entry.get("category") == category):
                if entry["action"] == "like":
                    score += 1
                elif entry["action"] == "dislike":
                    score -= 1
        return score
