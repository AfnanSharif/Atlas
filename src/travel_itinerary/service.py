from __future__ import annotations

from typing import Any, Protocol

from .catalog import ActivityCatalog
from .models import DayPlan, Itinerary, TripRequest
from .planner import ItineraryPlanner
from .feedback import VisualFeedbackStore


class ImageProvider(Protocol):
    def generate(self, prompt: str, **options: Any) -> Any: ...


class PromptRefiner(Protocol):
    def refine(self, prompt: str) -> str: ...


class TravelService:
    def __init__(
        self,
        catalog: ActivityCatalog | None = None,
        planner: ItineraryPlanner | None = None,
        image_provider: ImageProvider | None = None,
        prompt_refiner: PromptRefiner | None = None,
        feedback_store: VisualFeedbackStore | None = None,
    ) -> None:
        self.catalog = catalog or ActivityCatalog()
        self.planner = planner or ItineraryPlanner()
        self.image_provider = image_provider
        self.prompt_refiner = prompt_refiner
        self.feedback_store = feedback_store

    def create(self, request: TripRequest) -> Itinerary:
        return self.planner.plan(request, self.catalog.get(request.destination))

    def render_visual(self, day: DayPlan, destination: str = "", edit_instruction: str = "") -> tuple[str, Any]:
        """Refine and render a day prompt through the explicitly selected adapters."""
        if self.image_provider is None:
            raise RuntimeError("No image provider is configured")
        prompt = self.prompt_refiner.refine(day.visual_prompt) if self.prompt_refiner else day.visual_prompt
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("The prompt refiner returned an empty prompt")
        if self.feedback_store and destination:
            hint = self.feedback_store.preference_hint(destination)
            if hint:
                prompt = f"{prompt}. {hint}"
        image = self.image_provider.generate(prompt, title=day.title)
        if edit_instruction.strip():
            editor = getattr(self.image_provider, "edit", None)
            if not callable(editor):
                raise RuntimeError("The selected visual provider does not support InstructPix2Pix enhancement")
            image = editor(image, edit_instruction.strip())
        return prompt, image

    def record_visual_feedback(self, destination: str, day: DayPlan, prompt: str, rating: int, note: str = "") -> int:
        if self.feedback_store is None:
            raise RuntimeError("No feedback store is configured")
        return self.feedback_store.record(destination, day.day, prompt, rating, note)
