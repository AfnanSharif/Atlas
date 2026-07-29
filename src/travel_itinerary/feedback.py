from __future__ import annotations

import re
import sqlite3
from pathlib import Path


class VisualFeedbackStore:
    """Persistent human ratings that can refine later prompts for a destination."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS visual_feedback ("
                "id INTEGER PRIMARY KEY, destination TEXT NOT NULL, day INTEGER NOT NULL, "
                "prompt TEXT NOT NULL, rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5), note TEXT NOT NULL, "
                "created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
            )

    def record(self, destination: str, day: int, prompt: str, rating: int, note: str = "") -> int:
        destination, prompt, note = destination.strip(), prompt.strip(), note.strip()
        if not destination or not prompt or not 1 <= rating <= 5 or not 1 <= day <= 14:
            raise ValueError("destination, day, prompt, and a 1–5 rating are required")
        with sqlite3.connect(self.path) as connection:
            cursor = connection.execute(
                "INSERT INTO visual_feedback(destination, day, prompt, rating, note) VALUES (?, ?, ?, ?, ?)",
                (destination[:120], day, prompt[:4000], rating, note[:500]),
            )
            return int(cursor.lastrowid)

    def preference_hint(self, destination: str) -> str:
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                "SELECT note FROM visual_feedback WHERE lower(destination)=lower(?) AND rating >= 4 AND note != '' ORDER BY id DESC LIMIT 20",
                (destination.strip(),),
            ).fetchall()
        stop = {"about", "after", "again", "image", "more", "please", "should", "that", "this", "very", "with"}
        counts: dict[str, int] = {}
        for (note,) in rows:
            for token in re.findall(r"[A-Za-z][A-Za-z-]{2,}", note.lower()):
                if token not in stop:
                    counts[token] = counts.get(token, 0) + 1
        preferred = sorted(counts, key=lambda token: (-counts[token], token))[:6]
        return "Prior positive feedback favors: " + ", ".join(preferred) if preferred else ""
