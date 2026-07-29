from __future__ import annotations

import json
from pathlib import Path

from .models import Activity


class ActivityCatalog:
    """Loads a small curated catalog and creates sensible local fallbacks."""

    def __init__(self, path: str | Path | None = None) -> None:
        default = Path(__file__).resolve().parents[2] / "data" / "destinations.json"
        self.path = Path(path) if path else default
        self._data = json.loads(self.path.read_text(encoding="utf-8"))

    @property
    def destinations(self) -> tuple[str, ...]:
        return tuple(sorted(self._data))

    def get(self, destination: str) -> list[Activity]:
        key = next((name for name in self._data if name.casefold() == destination.casefold()), None)
        rows = self._data.get(key, []) if key else self._generic(destination)
        return [
            Activity(
                name=row["name"],
                description=row["description"],
                neighborhood=row["neighborhood"],
                duration_hours=float(row["duration_hours"]),
                cost_level=int(row["cost_level"]),
                themes=tuple(row["themes"]),
                indoor=bool(row.get("indoor", False)),
                accessible=bool(row.get("accessible", True)),
                best_time=row.get("best_time", "any"),
                tip=row.get("tip", ""),
            )
            for row in rows
        ]

    @staticmethod
    def _generic(destination: str) -> list[dict[str, object]]:
        templates = [
            ("Historic center walk", "A self-guided orientation through landmarks and local streets.", "Old Town", 2, 1, ["culture", "history"], "morning"),
            ("Local market tasting", "Meet independent vendors and sample regional specialties.", "Market District", 2, 2, ["food", "culture"], "morning"),
            ("City viewpoint", "Take in the skyline during the soft evening light.", "High Point", 1.5, 1, ["photography", "nature"], "evening"),
            ("Contemporary museum", "Explore art, design, and stories from the region.", "Museum Quarter", 2.5, 2, ["art", "culture"], "afternoon"),
            ("Neighborhood food trail", "A flexible route through well-reviewed independent eateries.", "Local Quarter", 2.5, 2, ["food"], "evening"),
            ("Urban nature escape", "Slow down in a major park or nearby natural reserve.", "Green District", 3, 1, ["nature", "wellness"], "afternoon"),
            ("Craft workshop", "Learn a local craft in a small hands-on session.", "Creative Quarter", 2, 2, ["art", "family"], "afternoon"),
            ("Day-trip sampler", f"Choose a well-connected small town or landscape outside {destination}.", "Region", 6, 3, ["adventure", "nature"], "morning"),
        ]
        return [
            {"name": name, "description": desc, "neighborhood": hood, "duration_hours": duration,
             "cost_level": cost, "themes": themes, "best_time": time, "accessible": duration < 6}
            for name, desc, hood, duration, cost, themes, time in templates
        ]
