"""Unit tests for IdempotencyService."""

import pytest

from app.services.idempotency import IdempotencyService


@pytest.mark.asyncio
async def test_idempotency_service_lock():
    provider = "github"
    repository = "owner/test-repo"
    delivery_id = "unique-delivery-uuid-999"

    # First attempt -> New delivery (Lock acquired = True)
    first_attempt = await IdempotencyService.check_and_lock(provider, repository, delivery_id)
    assert first_attempt is True

    # Second attempt with same delivery_id -> Duplicate delivery (Suppressed = False)
    second_attempt = await IdempotencyService.check_and_lock(provider, repository, delivery_id)
    assert second_attempt is False
