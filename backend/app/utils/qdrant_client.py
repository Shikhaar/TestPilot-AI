"""TestPilot AI — Qdrant Vector Database Client and Collection Management."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Get a cached Qdrant client instance.

    Returns:
        Configured QdrantClient connected to the Qdrant server.
    """
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=30,
    )
    logger.info("Qdrant client initialized", url=settings.qdrant_url)
    return client


# Collection configurations
COLLECTIONS: dict[str, dict[str, Any]] = {
    settings.qdrant_collection_repository_chunks: {
        "size": settings.embedding_dimensions,
        "distance": Distance.COSINE,
    },
    settings.qdrant_collection_functions: {
        "size": 384,  # all-MiniLM-L6-v2 dimension
        "distance": Distance.COSINE,
    },
    settings.qdrant_collection_classes: {
        "size": 384,
        "distance": Distance.COSINE,
    },
    settings.qdrant_collection_tests: {
        "size": 384,
        "distance": Distance.COSINE,
    },
    settings.qdrant_collection_bug_history: {
        "size": 384,
        "distance": Distance.COSINE,
    },
    settings.qdrant_collection_pr_reviews: {
        "size": 384,
        "distance": Distance.COSINE,
    },
}


async def initialize_collections(client: QdrantClient) -> None:
    """Create Qdrant collections if they don't already exist.

    Args:
        client: The Qdrant client instance.
    """
    existing = {c.name for c in client.get_collections().collections}

    for collection_name, config in COLLECTIONS.items():
        if collection_name not in existing:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=config["distance"],
                ),
            )
            logger.info("Qdrant collection created", collection=collection_name)
        else:
            logger.debug("Qdrant collection already exists", collection=collection_name)
