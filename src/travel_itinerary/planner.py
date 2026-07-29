from __future__ import annotations

import hashlib
from datetime import timedelta

from .models import Activity, DayPlan, Itinerary, ScheduledActivity, TripRequest
from .prompts import build_day_prompt


SLOTS = {
    "relaxed": ("10:00", "14:30"),
    "balanced": ("09:30", "13:30", "17:00"),
    "packed": ("08:30", "11:30", "15:00", "18:30"),
}
COST_LABELS = {1: "$", 2: "$$", 3: "$$$"}


def _minutes(clock: str) -> int:
    hour, minute = map(int, clock.split(":"))
    return hour * 60 + minute


def _clock(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


class ItineraryPlanner:
    """Deterministic constraint-aware planner; no network or model required."""

    def plan(self, request: TripRequest, activities: list[Activity]) -> Itinerary:
        eligible = [a for a in activities if not request.accessibility or a.accessible]
        if not eligible:
            raise ValueError("no activities match the accessibility preference")
        ranked = sorted(eligible, key=lambda a: self._rank(a, request), reverse=True)
        slot_count = len(SLOTS[request.pace])
        if len(ranked) < slot_count:
            raise ValueError(f"the catalog needs at least {slot_count} matching activities for a {request.pace} day")
        buckets: dict[int, list[Activity]] = {}
        # Group nearby activities while rotating neighborhoods between days.
        neighborhoods = list(dict.fromkeys(a.neighborhood for a in ranked))
        for day in range(request.days):
            target = neighborhoods[day % len(neighborhoods)]
            offset = day * slot_count % len(ranked)
            rotated = ranked[offset:] + ranked[:offset]
            nearby = [activity for activity in rotated if activity.neighborhood == target]
            rest = [activity for activity in rotated if activity.neighborhood != target]
            buckets[day] = (nearby + rest)[:slot_count]

        days: list[DayPlan] = []
        for index in range(request.days):
            chosen = buckets[index]
            long_activity = next((activity for activity in chosen if activity.duration_hours >= 5), None)
            if long_activity:
                evening = next(
                    (activity for activity in chosen if activity != long_activity and activity.best_time == "evening" and activity.duration_hours <= 3),
                    None,
                )
                chosen = [long_activity, *([evening] if evening else [])]
            ordered = sorted(chosen, key=lambda a: self._time_order(a.best_time))
            scheduled = self._schedule_day(ordered, request.pace)
            dominant = max(set(a.neighborhood for a in chosen), key=lambda hood: sum(a.neighborhood == hood for a in chosen))
            themes = sorted({theme for a in chosen for theme in a.themes})[:2]
            trip_date = request.start_date + timedelta(days=index) if request.start_date else None
            days.append(
                DayPlan(
                    day=index + 1,
                    title=f"{dominant}: {' & '.join(theme.title() for theme in themes)}",
                    date=trip_date.isoformat() if trip_date else None,
                    neighborhood_focus=dominant,
                    activities=scheduled,
                    estimated_cost=COST_LABELS[round(sum(a.cost_level for a in chosen) / len(chosen))],
                    visual_prompt=build_day_prompt(request, index + 1, chosen),
                )
            )
        profile = f"{request.travelers.title()} · {request.pace.title()} pace · {request.budget.title()}"
        notes = ["Times are planning estimates; confirm hours and reservations before travel."]
        if request.accessibility:
            notes.append("Only catalog activities marked step-free/accessibility-friendly were selected.")
        if request.destination not in {"Kyoto", "Lisbon", "Cape Town"}:
            notes.append("This destination uses the generic local-exploration catalog; replace suggestions with verified local venues.")
        return Itinerary(
            destination=request.destination,
            summary=f"A {request.days}-day {', '.join(request.themes)} itinerary designed for {request.travelers} travelers.",
            traveler_profile=profile,
            days=tuple(days),
            planning_notes=tuple(notes),
        )

    @staticmethod
    def _rank(activity: Activity, request: TripRequest) -> tuple[float, str]:
        overlap = len(set(activity.themes) & set(request.themes))
        target_cost = {"budget": 1, "mid-range": 2, "luxury": 3}.get(request.budget, 2)
        cost_fit = 2 - abs(activity.cost_level - target_cost)
        party_fit = int(request.travelers in activity.themes or "family" not in activity.themes)
        digest = hashlib.sha1(f"{request.destination}:{activity.name}".encode()).hexdigest()
        return overlap * 5 + cost_fit + party_fit, digest

    @staticmethod
    def _time_order(best_time: str) -> int:
        return {"morning": 0, "afternoon": 1, "evening": 2, "any": 1}.get(best_time, 1)

    @staticmethod
    def _schedule_day(activities: list[Activity], pace: str) -> tuple[ScheduledActivity, ...]:
        scheduled = []
        previous_end = 0
        for suggested, activity in zip(SLOTS[pace], activities):
            # Keep at least 30 minutes for local transit after the first stop.
            preferred_floor = {"afternoon": "13:00", "evening": "17:00"}.get(activity.best_time, suggested)
            start_minutes = max(_minutes(suggested), _minutes(preferred_floor), previous_end + (30 if scheduled else 0))
            end_minutes = start_minutes + int(activity.duration_hours * 60)
            scheduled.append(ScheduledActivity(_clock(start_minutes), _clock(end_minutes), activity))
            previous_end = end_minutes
        return tuple(scheduled)
