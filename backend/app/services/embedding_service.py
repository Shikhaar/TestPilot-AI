"""
TestPilot AI — Embedding Service.

Handles generating vector embeddings for code chunks and functions.
Supports local SentenceTransformer embeddings or cloud-based LiteLLM embeddings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import litellm

from app.core.config import get_settings
from app.core.logging import get_logger

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[misc, assignment]

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating vector embeddings of text and code."""

    def __init__(self) -> None:
        self.use_local = settings.use_local_embeddings
        self._local_model: Any | None = None

    def _get_hash_vector(self, text: str, dim: int = 384) -> list[float]:
        """Generate a deterministic normalized pseudo-random float vector from text hash."""
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(dim):
            byte_val = h[i % len(h)]
            vec.append((byte_val / 255.0) - 0.5)
        return vec

    def generate_embedding(self, text: str) -> list[float]:
        """Generate a single vector embedding for the input text."""
        if self.use_local:
            if SentenceTransformer is not None:
                try:
                    if self._local_model is None:
                        self._local_model = SentenceTransformer(settings.sentence_transformer_model)
                    return self._local_model.encode(text).tolist()
                except Exception as e:
                    logger.warning("Local SentenceTransformer failed, using hash vector", error=str(e))
            return self._get_hash_vector(text, 384)
        else:
            try:
                response = litellm.embedding(
                    model=settings.litellm_default_model,
                    input=[text],
                )
                return response.data[0]["embedding"]
            except Exception as e:
                logger.warning(
                    "Cloud embedding generation failed, falling back to hash vector",
                    error=str(e),
                )
                return self._get_hash_vector(text, 384)

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a batch of texts."""
        if not texts:
            return []

        if self.use_local:
            model = self._get_local_model()
            vectors = model.encode(texts).tolist()
            return vectors
        else:
            try:
                response = litellm.embedding(
                    model=settings.litellm_default_model,
                    input=texts,
                )
                return [item["embedding"] for item in response.data]
            except Exception as e:
                logger.warning(
                    "Batch cloud embedding failed, falling back to sequential local/mock",
                    error=str(e),
                )
                return [self.generate_embedding(t) for t in texts]


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Get a cached EmbeddingService instance."""
    return EmbeddingService()
