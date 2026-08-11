"""Unit tests for GitLabWebhookAdapter."""

import json

from app.utils.webhook_adapters import GitLabWebhookAdapter


def test_gitlab_adapter_parse():
    adapter = GitLabWebhookAdapter()
    headers = {"x-gitlab-event-uuid": "gl-event-7777"}
    body = json.dumps(
        {
            "object_attributes": {
                "id": 88,
                "iid": 12,
                "action": "update",
                "source_branch": "gl-feature",
                "target_branch": "main",
                "last_commit": {"id": "gl_head_sha"},
                "target_commit": "gl_base_sha",
            },
            "project": {"id": 901, "path_with_namespace": "group/gitlab-repo"},
            "user": {"username": "gluser"},
        }
    ).encode("utf-8")

    assert adapter.extract_delivery_id(headers, body) == "gl-event-7777"

    event = adapter.parse(headers, body)
    assert event.provider == "gitlab"
    assert event.action == "synchronize"  # Normalized GitLab 'update' -> 'synchronize'
    assert event.repository == "group/gitlab-repo"
    assert event.pull_request_id == "12"
    assert event.author == "gluser"
