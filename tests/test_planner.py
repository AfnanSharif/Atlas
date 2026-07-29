import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from travel_itinerary.models import TripRequest
from travel_itinerary.feedback import VisualFeedbackStore
from travel_itinerary.service import TravelService


class PlannerTests(unittest.TestCase):
    def test_balanced_plan_is_complete_and_serializable(self):
        plan = TravelService().create(TripRequest("Kyoto", days=2, start_date=date(2027, 4, 1)))
        self.assertEqual(len(plan.days), 2)
        self.assertTrue(all(len(day.activities) == 3 for day in plan.days))
        self.assertEqual(plan.days[1].date, "2027-04-02")
        json.dumps(plan.to_dict())

    def test_generic_destination_works_without_network(self):
        plan = TravelService().create(TripRequest("Lahore", days=1, themes=("food",), pace="relaxed"))
        self.assertEqual(plan.destination, "Lahore")
        self.assertEqual(len(plan.days[0].activities), 2)
        self.assertTrue(any("generic" in note for note in plan.planning_notes))

    def test_validation_rejects_unsafe_duration(self):
        with self.assertRaises(ValueError):
            TripRequest("Kyoto", days=30)

    def test_accessible_filter(self):
        plan = TravelService().create(TripRequest("Kyoto", days=1, accessibility=True))
        self.assertTrue(all(item.activity.accessible for item in plan.days[0].activities))

    def test_maximum_packed_plan_fills_every_day(self):
        plan = TravelService().create(TripRequest("Lisbon", days=14, pace="packed"))
        self.assertEqual(len(plan.days), 14)
        self.assertTrue(all(len(day.activities) == 4 for day in plan.days))
        self.assertTrue(all(len({item.activity.name for item in day.activities}) == 4 for day in plan.days))

    def test_long_activity_does_not_overlap_next_stop(self):
        plan = TravelService().create(TripRequest("Cape Town", days=5, pace="packed", themes=("nature", "adventure")))
        for day in plan.days:
            previous_end = -1
            for item in day.activities:
                start = int(item.start[:2]) * 60 + int(item.start[3:])
                end = int(item.end[:2]) * 60 + int(item.end[3:])
                self.assertGreater(start, previous_end)
                self.assertLessEqual(end, 24 * 60)
                previous_end = end

    def test_visual_adapters_are_invoked_by_service(self):
        class FakeRefiner:
            def __init__(self):
                self.calls = []

            def refine(self, prompt):
                self.calls.append(prompt)
                return "refined: " + prompt

        class FakeImageProvider:
            def __init__(self):
                self.calls = []

            def generate(self, prompt, **options):
                self.calls.append((prompt, options))
                return "fake-image"

        refiner, provider = FakeRefiner(), FakeImageProvider()
        service = TravelService(image_provider=provider, prompt_refiner=refiner)
        day = service.create(TripRequest("Kyoto", days=1)).days[0]
        prompt, image = service.render_visual(day)
        self.assertEqual(image, "fake-image")
        self.assertTrue(prompt.startswith("refined: "))
        self.assertEqual(len(refiner.calls), 1)
        self.assertEqual(provider.calls[0][0], prompt)

    def test_feedback_loop_and_pix2pix_edit_are_reachable(self):
        class FakeEditor:
            def __init__(self):
                self.edits = []

            def generate(self, prompt, **options):
                return {"prompt": prompt}

            def edit(self, image, instruction):
                self.edits.append(instruction)
                return {**image, "edit": instruction}

        with tempfile.TemporaryDirectory() as folder:
            store = VisualFeedbackStore(Path(folder) / "feedback.db")
            provider = FakeEditor()
            service = TravelService(image_provider=provider, feedback_store=store)
            day = service.create(TripRequest("Kyoto", days=1)).days[0]
            service.record_visual_feedback("Kyoto", day, day.visual_prompt, 5, "Favor warm lantern light")
            prompt, image = service.render_visual(day, "Kyoto", "Add gentle rain")
            self.assertIn("warm", prompt)
            self.assertEqual(image["edit"], "Add gentle rain")
            self.assertEqual(provider.edits, ["Add gentle rain"])


if __name__ == "__main__":
    unittest.main()
