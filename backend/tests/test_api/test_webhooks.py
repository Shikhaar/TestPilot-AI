"""TestPilot AI — GitHub Webhook API Tests."""

from __future__ import annotations

import hashlib
import hmac
import json

import pytest
from httpx import AsyncClient


def sign_payload(payload: bytes, secret: str) -> str:
    """Generate a GitHub webhook HMAC-SHA256 signature."""
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


from app.core.config import get_settings

WEBHOOK_SECRET = get_settings().github_webhook_secret


@pytest.mark.asyncio
@pytest.mark.unit
async def test_webhook_ping(client: AsyncClient) -> None:
    """Test GitHub webhook ping event."""
    payload = json.dumps({"zen": "Keep it logically awesome."}).encode()
    signature = sign_payload(payload, WEBHOOK_SECRET)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "test-delivery-001",
        },
    )
    assert response.status_code == 202
    assert response.json()["status"] == "pong"


@pytest.mark.asyncio
@pytest.mark.unit
async def test_webhook_invalid_signature(client: AsyncClient) -> None:
    """Test that invalid signatures return 403."""
    payload = json.dumps({"action": "opened"}).encode()

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid_signature",
            "X-GitHub-Event": "pull_request",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.unit
async def test_webhook_missing_signature(client: AsyncClient) -> None:
    """Test that missing signatures return 403."""
    payload = json.dumps({"action": "opened"}).encode()

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={"Content-Type": "application/json", "X-GitHub-Event": "pull_request"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.unit
async def test_webhook_pr_opened_unregistered_repo(client: AsyncClient) -> None:
    """Test PR event for unregistered repository is accepted but does nothing."""
    payload = json.dumps(
        {
            "action": "opened",
            "pull_request": {
                "id": 1,
                "number": 1,
                "title": "Test PR",
                "state": "open",
                "user": {"login": "dev"},
                "base": {"ref": "main", "sha": "aaa"},
                "head": {"ref": "feature", "sha": "bbb"},
                "body": None,
                "changed_files": 1,
                "additions": 10,
                "deletions": 2,
            },
            "repository": {"id": 99, "full_name": "unregistered/repo"},
            "installation": {"id": 1},
        }
    ).encode()

    signature = sign_payload(payload, WEBHOOK_SECRET)

    response = await client.post(
        "/api/v1/webhooks/github",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
            "X-GitHub-Event": "pull_request",
            "X-GitHub-Delivery": "test-delivery-002",
        },
    )
    # Should accept the webhook even for unregistered repos
    assert response.status_code == 202
