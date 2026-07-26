"""
Embedder factory: selects the active image-embedding backend.

`EMBEDDER_BACKEND` env var:
  - "gemini"  (default) -> GeminiImageEmbedder (Gemini Embedding 2, no GPU required)
  - "openclip"          -> ImageEmbedder3 (local OpenCLIP; kept for eval A/B comparison)

Centralizes the choice so main.py and scripts/eval_retrieval.py stay in sync.
"""

import os


def create_embedder(device=None):
    backend = os.getenv("EMBEDDER_BACKEND", "gemini").strip().lower()

    if backend == "openclip":
        from image_embedder3 import ImageEmbedder3

        preset = os.getenv("MODEL_PRESET", "balanced")
        return ImageEmbedder3(preset=preset, device=device)

    if backend == "gemini":
        from gemini_embedder import GeminiImageEmbedder

        return GeminiImageEmbedder(device=device)

    raise ValueError(
        f"Unknown EMBEDDER_BACKEND={backend!r}. Expected 'gemini' or 'openclip'."
    )
