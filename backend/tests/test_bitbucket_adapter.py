"""Unit tests for BitbucketWebhookAdapter."""

import json

from app.utils.webhook_adapters import BitbucketWebhookAdapter


def test_bitbucket_adapter_normalize_action():
    adapter = BitbucketWebhookAdapter()
    headers = {"x-hook-uuid": "{uuid-bb-9999}", "x-event-key": "pullrequest:updated"}
    body = json.dumps(
        {
            "repository": {"uuid": "{repo-uuid-111}", "full_name": "workspace/bitbucket-repo"},
            "pullrequest": {
                "id": 15,
                "source": {"branch": {"name": "feature-bb"}, "commit": {"hash": "bb_head_sha"}},
                "destination": {"branch": {"name": "master"}, "commit": {"hash": "bb_base_sha"}},
                "author": {"nickname": "bbuser"},
            },
        }
    ).encode("utf-8")

    assert adapter.verify(headers, body) is True
    assert adapter.extract_delivery_id(headers, body) == "uuid-bb-9999"

    event = adapter.parse(headers, body)
    assert event.provider == "bitbucket"
    assert event.action == "synchronize"  # Normalized Bitbucket 'updated' -> 'synchronize'
    assert event.repository == "workspace/bitbucket-repo"
    assert event.delivery_id == "uuid-bb-9999"
    assert event.pull_request_id == "15"
    assert event.author == "bbuser"
