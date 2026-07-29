from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class TripRequest:
    destination: str
    days: int = 3
    travelers: str = "couple"
    themes: tuple[str, ...] = ("culture", "food")
    pace: str = "balanced"
    budget: str = "mid-range"
    season: str = "spring"
    accessibility: bool = False
    start_date: date | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.destination.strip():
            raise ValueError("destination is required")
        if not 1 <= self.days <= 14:
            raise ValueError("days must be between 1 and 14")
        if not self.themes:
            raise ValueError("at least one travel theme is required")
        if self.pace not in {"relaxed", "balanced", "packed"}:
            raise ValueError("pace must be relaxed, balanced, or packed")
        if self.travelers not in {"solo", "couple", "family", "friends"}:
            raise ValueError("unsupported traveler type")
        if self.budget not in {"budget", "mid-range", "luxury"}:
            raise ValueError("budget must be budget, mid-range, or luxury")


@dataclass(frozen=True)
class Activity:
    name: str
    description: str
    neighborhood: str
    duration_hours: float
    cost_level: int
    themes: tuple[str, ...]
    indoor: bool = False
    accessible: bool = True
    best_time: str = "any"
    tip: str = ""


@dataclass(frozen=True)
class ScheduledActivity:
    start: str
    end: str
    activity: Activity


@dataclass(frozen=True)
class DayPlan:
    day: int
    title: str
    date: str | None
    neighborhood_focus: str
    activities: tuple[ScheduledActivity, ...]
    estimated_cost: str
    visual_prompt: str


@dataclass(frozen=True)
class Itinerary:
    destination: str
    summary: str
    traveler_profile: str
    days: tuple[DayPlan, ...]
    planning_notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
