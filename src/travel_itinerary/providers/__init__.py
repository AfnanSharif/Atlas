"""Optional image and prompt providers. Imports stay lazy for offline use."""

import os

from .diffusion import DiffusionImageProvider, PlaceholderImageProvider
from .gemini import GeminiPromptRefiner

__all__ = ["DiffusionImageProvider", "PlaceholderImageProvider", "GeminiPromptRefiner"]


def create_image_provider(name: str | None = None):
    """Build the selected image adapter without importing model runtimes eagerly."""
    selected = (name or os.getenv("IMAGE_PROVIDER", "placeholder")).strip().lower()
    if selected == "placeholder":
        return PlaceholderImageProvider()
    if selected in {"diffusion", "sdxl", "stable-diffusion"}:
        return DiffusionImageProvider(
            model_id=os.getenv("DIFFUSION_MODEL_ID", "stabilityai/stable-diffusion-xl-base-1.0"),
            device=os.getenv("DIFFUSION_DEVICE", "cpu"),
            edit_model_id=os.getenv("PIX2PIX_MODEL_ID", "timbrooks/instruct-pix2pix"),
        )
    raise ValueError("IMAGE_PROVIDER must be placeholder or diffusion")


def create_prompt_refiner(name: str | None = None):
    selected = (name or os.getenv("PROMPT_REFINER", "none")).strip().lower()
    if selected in {"", "none", "local"}:
        return None
    if selected == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini prompt refinement")
        return GeminiPromptRefiner(api_key, os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    raise ValueError("PROMPT_REFINER must be none or gemini")


__all__ += ["create_image_provider", "create_prompt_refiner"]
