from __future__ import annotations

from .models import Activity, TripRequest


def build_day_prompt(request: TripRequest, day: int, activities: list[Activity]) -> str:
    landmarks = ", ".join(a.name for a in activities[:3])
    return (
        f"Editorial travel photograph of {request.destination} in {request.season}, day {day}; "
        f"inspired by {landmarks}; {', '.join(request.themes)} mood; suitable for {request.travelers} travelers; "
        "natural light, authentic local atmosphere, human-scale composition, realistic colors, no text, no logos"
    )


def edit_instruction(request: TripRequest) -> str:
    return (
        f"Transform this image into an authentic {request.season} scene in {request.destination}; "
        f"preserve the composition, emphasize {', '.join(request.themes)}, avoid stereotypes and visible text."
    )
