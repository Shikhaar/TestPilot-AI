"""TestPilot AI — Webhook Idempotency Service."""

from __future__ import annotations

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class IdempotencyService:
    """Infrastructure service to enforce idempotency for webhook delivery IDs."""

    @staticmethod
    async def check_and_lock(
        provider: str, repository: str, delivery_id: str, ttl_seconds: int = 86400
    ) -> bool:
        """Check if delivery ID has already been processed. If not, set atomic lock.

        Args:
            provider: VCS provider name (github, bitbucket, etc.)
            repository: Full repository name (owner/repo)
            delivery_id: Provider delivery/event UUID
            ttl_seconds: Lock expiration in seconds (default: 24h)

        Returns:
            True if this is a NEW event (lock acquired).
            False if this is a DUPLICATE event (already processed).
        """
        if not delivery_id or delivery_id == "unknown":
            # If provider did not supply a delivery ID, permit execution to proceed
            return True

        key = f"webhook:{provider.lower()}:{repository.lower()}:{delivery_id}"
        try:
            r = aioredis.from_url(settings.redis_url)
            # set nx=True returns True if key was set (new), None if key already existed (duplicate)
            acquired = await r.set(key, "1", nx=True, ex=ttl_seconds)
            await r.close()
            return bool(acquired)
        except Exception as e:
            logger.warning(
                "Redis idempotency check failed (falling back to allowing delivery)",
                key=key,
                error=str(e),
            )
            return True
