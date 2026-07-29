from __future__ import annotations


class GeminiPromptRefiner:
    """Opt-in Gemini adapter for richer art direction without itinerary changes."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("Install google-genai to enable Gemini prompt refinement") from exc
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def refine(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                "Refine the following travel image prompt for a photorealistic diffusion model. "
                "Keep every named place unchanged, do not invent landmarks, avoid cultural stereotypes, visible text, or logos. "
                "Return only one concise prompt.\n\n" + prompt
            ),
        )
        refined = (response.text or "").strip()
        if not refined:
            raise ValueError("Gemini returned an empty prompt")
        return refined
