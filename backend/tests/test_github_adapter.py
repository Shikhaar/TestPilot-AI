"""Unit tests for GitHubWebhookAdapter."""

import json

from app.utils.webhook_adapters import GitHubWebhookAdapter


def test_github_adapter_parse():
    adapter = GitHubWebhookAdapter()
    headers = {"x-github-delivery": "delivery-gh-12345"}
    body = json.dumps(
        {
            "action": "synchronize",
            "number": 42,
            "repository": {"id": 1001, "full_name": "owner/repo"},
            "pull_request": {
                "id": 5001,
                "number": 42,
                "head": {"sha": "head_sha_123", "ref": "feature-branch"},
                "base": {"sha": "base_sha_456", "ref": "main"},
                "user": {"login": "testuser"},
            },
        }
    ).encode("utf-8")

    assert adapter.verify(headers, body) is True
    assert adapter.extract_delivery_id(headers, body) == "delivery-gh-12345"

    event = adapter.parse(headers, body)
    assert event.provider == "github"
    assert event.action == "synchronize"
    assert event.repository == "owner/repo"
    assert event.delivery_id == "delivery-gh-12345"
    assert event.pull_request_id == "42"
    assert event.head_sha == "head_sha_123"
    assert event.author == "testuser"
