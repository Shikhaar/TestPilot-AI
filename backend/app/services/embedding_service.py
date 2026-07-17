"""
TestPilot AI — Embedding Service.

Handles generating vector embeddings for code chunks and functions.
Supports local SentenceTransformer embeddings or cloud-based LiteLLM embeddings.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating vector embeddings of text and code."""

    def __init__(self) -> None:
        self.use_local = settings.use_local_embeddings
        self._local_model = None

    def _get_local_model(self) -> Any:
        """Lazy-load the SentenceTransformer model to save memory on start."""
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._local_model = SentenceTransformer(settings.sentence_transformer_model)
                logger.info(
                    "SentenceTransformer model loaded", model=settings.sentence_transformer_model
                )
            except ImportError as e:
                logger.error("Failed to load sentence-transformers library", error=str(e))
                raise RuntimeError(
                    "sentence-transformers not installed. Install it or set USE_LOCAL_EMBEDDINGS=False"
                ) from e
        return self._local_model

    def generate_embedding(self, text: str) -> list[float]:
        """Generate a single vector embedding for the input text."""
        if self.use_local:
            model = self._get_local_model()
            vector = model.encode(text).tolist()
            return vector
        else:
            try:
                import litellm

                response = litellm.embedding(
                    model=settings.litellm_default_model,  # e.g. text-embedding-3-small
                    input=[text],
                )
                return response.data[0]["embedding"]
            except Exception as e:
                logger.warning(
                    "Cloud embedding generation failed, falling back to local if possible",
                    error=str(e),
                )
                # Fallback to local if installed
                try:
                    model = self._get_local_model()
                    return model.encode(text).tolist()
                except Exception:
                    # Return zero vector fallback
                    logger.error("No embedding options available, returning zero vector")
                    return [0.0] * settings.embedding_dimensions

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
                import litellm

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
