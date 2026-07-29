from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

from .models import TripRequest
from .feedback import VisualFeedbackStore
from .providers import create_image_provider, create_prompt_refiner
from .service import TravelService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a personalized offline travel itinerary")
    parser.add_argument("destination")
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--travelers", default="couple", choices=["solo", "couple", "family", "friends"])
    parser.add_argument("--themes", default="culture,food")
    parser.add_argument("--pace", default="balanced", choices=["relaxed", "balanced", "packed"])
    parser.add_argument("--budget", default="mid-range", choices=["budget", "mid-range", "luxury"])
    parser.add_argument("--season", default="spring")
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--accessible", action="store_true")
    parser.add_argument("--image-provider", choices=["placeholder", "diffusion"], default=os.getenv("IMAGE_PROVIDER", "placeholder"))
    parser.add_argument("--prompt-refiner", choices=["none", "gemini"], default=os.getenv("PROMPT_REFINER", "none"))
    parser.add_argument("--render-dir", type=Path, help="render one SVG/PNG visual per day")
    parser.add_argument("--edit-instruction", default=os.getenv("VISUAL_EDIT_INSTRUCTION", ""), help="optional InstructPix2Pix enhancement")
    parser.add_argument("--feedback-db", type=Path, default=Path(os.getenv("FEEDBACK_DB", ".local/visual-feedback.db")))
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass
    else:
        load_dotenv()

    args = build_parser().parse_args(argv)
    request = TripRequest(
        destination=args.destination, days=args.days, travelers=args.travelers,
        themes=tuple(filter(None, (item.strip() for item in args.themes.split(",")))),
        pace=args.pace, budget=args.budget, season=args.season,
        start_date=args.start_date, accessibility=args.accessible,
    )
    service = TravelService()
    itinerary = service.create(request)
    if args.render_dir:
        service = TravelService(
            catalog=service.catalog,
            planner=service.planner,
            image_provider=create_image_provider(args.image_provider),
            prompt_refiner=create_prompt_refiner(args.prompt_refiner),
            feedback_store=VisualFeedbackStore(args.feedback_db),
        )
        args.render_dir.mkdir(parents=True, exist_ok=True)
        for day in itinerary.days:
            _prompt, image = service.render_visual(day, itinerary.destination, args.edit_instruction)
            if isinstance(image, str):
                destination = args.render_dir / f"day-{day.day:02d}.svg"
                destination.write_text(image, encoding="utf-8")
            else:
                destination = args.render_dir / f"day-{day.day:02d}.png"
                image.save(destination)
            print(f"Rendered {destination}", file=sys.stderr)
    print(json.dumps(itinerary.to_dict(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
