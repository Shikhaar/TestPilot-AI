"""TestPilot AI — Repository API Tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_repositories_unauthorized(client: AsyncClient) -> None:
    """Test that unauthenticated requests return 401."""
    response = await client.get("/api/v1/repositories")
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.unit
async def test_list_repositories_empty(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test listing repositories returns empty list for new user."""
    response = await client.get("/api/v1/repositories", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_repository_not_found(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test getting a non-existent repository returns 404."""
    response = await client.get(
        "/api/v1/repositories/non-existent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.unit
async def test_get_repository_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
    test_repository: object,
) -> None:
    """Test getting an existing repository returns correct data."""
    response = await client.get(
        f"/api/v1/repositories/{test_repository.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == test_repository.id
    assert data["data"]["full_name"] == test_repository.full_name


@pytest.mark.asyncio
@pytest.mark.unit
async def test_health_check() -> None:
    """Test the health check endpoint returns healthy status."""
    # Health check doesn't need auth
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
