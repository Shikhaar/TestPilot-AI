"""Unit tests for AzureDevOpsWebhookAdapter."""

import json

from app.utils.webhook_adapters import AzureDevOpsWebhookAdapter


def test_azure_devops_adapter_parse():
    adapter = AzureDevOpsWebhookAdapter()
    headers = {"x-vss-subscription-id": "sub-ado-3333"}
    body = json.dumps(
        {
            "eventType": "git.pullrequest.updated",
            "resource": {
                "pullRequestId": 99,
                "sourceRefName": "refs/heads/ado-feature",
                "targetRefName": "refs/heads/main",
                "lastMergeSourceCommit": {"commitId": "ado_head_sha"},
                "lastMergeTargetCommit": {"commitId": "ado_base_sha"},
                "createdBy": {"uniqueName": "adouser@company.com"},
                "repository": {
                    "id": "repo-ado-55",
                    "name": "ado-repo",
                    "project": {"name": "my-project"},
                },
            },
        }
    ).encode("utf-8")

    assert adapter.extract_delivery_id(headers, body) == "sub-ado-3333"

    event = adapter.parse(headers, body)
    assert event.provider == "azure_devops"
    assert event.action == "synchronize"
    assert event.repository == "my-project/ado-repo"
    assert event.pull_request_id == "99"
    assert event.source_branch == "ado-feature"
    assert event.target_branch == "main"
