from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any


@dataclass
class PlaceholderImageProvider:
    """Creates a local SVG preview so a basic run never needs a GPU or key."""

    width: int = 1200
    height: int = 630

    def generate(self, prompt: str, title: str = "Travel story") -> str:
        safe_title = html.escape(title)
        safe_prompt = html.escape(prompt[:180])
        return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#0b132b"/><stop offset=".55" stop-color="#1c6e8c"/><stop offset="1" stop-color="#f2c14e"/></linearGradient></defs>
<rect width="100%" height="100%" rx="36" fill="url(#g)"/><circle cx="980" cy="150" r="100" fill="#fff" opacity=".15"/>
<path d="M0 510 Q260 340 520 500 T1200 430 V630 H0Z" fill="#071022" opacity=".75"/>
<text x="72" y="120" fill="#f8fafc" font-size="56" font-family="sans-serif" font-weight="700">{safe_title}</text>
<foreignObject x="72" y="170" width="880" height="180"><div xmlns="http://www.w3.org/1999/xhtml" style="color:#e2e8f0;font:26px sans-serif;line-height:1.45">{safe_prompt}</div></foreignObject>
<text x="72" y="570" fill="#fff" font-size="19" font-family="sans-serif" opacity=".8">LOCAL PREVIEW · connect Stable Diffusion for generated art</text></svg>'''


class DiffusionImageProvider:
    """Lazy adapter for Stable Diffusion and InstructPix2Pix pipelines."""

    def __init__(self, model_id: str = "stabilityai/stable-diffusion-xl-base-1.0", device: str = "cpu", edit_model_id: str = "timbrooks/instruct-pix2pix") -> None:
        self.model_id = model_id
        self.device = device
        self.edit_model_id = edit_model_id
        self._pipeline: Any = None
        self._edit_pipeline: Any = None

    def _load(self) -> Any:
        if self._pipeline is None:
            try:
                import torch
                from diffusers import AutoPipelineForText2Image
            except ImportError as exc:
                raise RuntimeError("Install the optional diffusion dependencies first") from exc
            dtype = torch.float16 if self.device.startswith("cuda") else torch.float32
            self._pipeline = AutoPipelineForText2Image.from_pretrained(self.model_id, torch_dtype=dtype).to(self.device)
        return self._pipeline

    def generate(self, prompt: str, **options: Any) -> Any:
        pipeline = self._load()
        allowed = {k: v for k, v in options.items() if k in {"height", "width", "num_inference_steps", "guidance_scale"}}
        return pipeline(prompt=prompt, **allowed).images[0]

    def edit(self, image: Any, instruction: str) -> Any:
        if not instruction.strip():
            raise ValueError("edit instruction is required")
        if self._edit_pipeline is None:
            try:
                import torch
                from diffusers import StableDiffusionInstructPix2PixPipeline
            except ImportError as exc:
                raise RuntimeError("Install diffusers, transformers, accelerate and torch") from exc
            dtype = torch.float16 if self.device.startswith("cuda") else torch.float32
            self._edit_pipeline = StableDiffusionInstructPix2PixPipeline.from_pretrained(self.edit_model_id, torch_dtype=dtype).to(self.device)
        return self._edit_pipeline(prompt=instruction, image=image).images[0]
