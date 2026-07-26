"""
Gemini Embedding 2 (natively multimodal) image embedder.

Drop-in replacement for the OpenCLIP `ImageEmbedder3`: exposes the same
`get_embedding(image_url)` interface plus `embed_dim` / `model_key` attributes so
`ImageUploader`, the search route, and `/api/database/stats` keep working unchanged.

Uses the same `google-genai` SDK and `GEMINI_API_KEY` already used by
`gemini_service.py`, so no extra GCP/Vertex setup is required.
"""

import os

import numpy as np
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-embedding-2-preview"
DEFAULT_DIM = 1536

# task_type asymmetry improves retrieval quality: catalog items are documents,
# search inputs are queries.
TASK_TYPE_DOCUMENT = "RETRIEVAL_DOCUMENT"
TASK_TYPE_QUERY = "RETRIEVAL_QUERY"


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class GeminiImageEmbedder:
    def __init__(self, model: str | None = None, dim: int | None = None, device=None):
        # `device` is accepted for interface compatibility with ImageEmbedder3; unused.
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.model_name = model or os.getenv("GEMINI_EMBED_MODEL", DEFAULT_MODEL)
        self.embed_dim = dim if dim is not None else _int_env("GEMINI_EMBED_DIM", DEFAULT_DIM)
        self.model_key = f"{self.model_name}::dim{self.embed_dim}"

        self.client = genai.Client(api_key=api_key)
        print(f"✅ Gemini embedder ready — model: {self.model_name}, dimension: {self.embed_dim}")

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        # Matryoshka-truncated outputs (<3072) are not unit-normalized by the API,
        # so normalize to keep cosine similarity consistent with the OpenCLIP path.
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def embed_bytes(
        self, data: bytes, mime_type: str = "image/jpeg", task_type: str = TASK_TYPE_DOCUMENT
    ) -> np.ndarray | None:
        """Embed raw image bytes into a normalized vector."""
        try:
            result = self.client.models.embed_content(
                model=self.model_name,
                contents=[types.Part.from_bytes(data=data, mime_type=mime_type)],
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self.embed_dim,
                ),
            )
            values = result.embeddings[0].values
            return self._normalize(np.array(values, dtype=np.float32))
        except Exception as e:
            print(f"❌ Gemini embed_bytes failed: {e}")
            return None

    def get_embedding(
        self,
        image_url: str,
        multi_crop: bool = False,
        task_type: str = TASK_TYPE_DOCUMENT,
    ) -> np.ndarray | None:
        """
        Fetch an image from a URL and return its normalized embedding.

        `multi_crop` is accepted for signature compatibility with ImageEmbedder3
        and ignored (managed model handles the full image).
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            mime_type = response.headers.get("Content-Type") or "image/jpeg"
            # Strip charset/params if present (e.g. "image/jpeg; charset=...").
            mime_type = mime_type.split(";")[0].strip() or "image/jpeg"
            return self.embed_bytes(response.content, mime_type, task_type)
        except Exception as e:
            print(f"❌ Error processing {image_url}: {e}")
            return None
