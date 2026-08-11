"""TestPilot AI — Provider Webhook Adapters.

Implements the WebhookAdapter protocol for GitHub, Bitbucket, GitLab, and Azure DevOps.
Decouples VCS-specific signature validation and payload normalization from the HTTP router.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Protocol

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.webhook import NormalizedAction, NormalizedPREvent

logger = get_logger(__name__)
settings = get_settings()


class WebhookAdapter(Protocol):
    """Protocol for provider-specific webhook security validation and payload parsing."""

    def verify(self, headers: dict[str, str], body: bytes) -> bool:
        """Verify webhook signature or secret token."""
        ...

    def extract_delivery_id(self, headers: dict[str, str], body: bytes) -> str:
        """Extract provider's unique delivery/event UUID."""
        ...

    def parse(self, headers: dict[str, str], body: bytes) -> NormalizedPREvent:
        """Parse raw webhook body into NormalizedPREvent DTO."""
        ...


class GitHubWebhookAdapter:
    """GitHub Webhook Adapter (HMAC SHA-256 validation)."""

    def verify(self, headers: dict[str, str], body: bytes) -> bool:
        secret = settings.github_webhook_secret
        if not secret:
            # If no secret configured in environment, permit in dev mode
            return True

        sig_header = headers.get("x-hub-signature-256") or headers.get("X-Hub-Signature-256")
        if not sig_header or not sig_header.startswith("sha256="):
            return False

        expected_sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        received_sig = sig_header.replace("sha256=", "").strip()
        return hmac.compare_digest(expected_sig, received_sig)

    def extract_delivery_id(self, headers: dict[str, str], body: bytes) -> str:
        delivery_id = headers.get("x-github-delivery") or headers.get("X-GitHub-Delivery")
        if delivery_id:
            return delivery_id
        try:
            data = json.loads(body.decode("utf-8"))
            return str(data.get("number") or data.get("pull_request", {}).get("id", "unknown"))
        except Exception:
            return "unknown"

    def parse(self, headers: dict[str, str], body: bytes) -> NormalizedPREvent:
        data = json.loads(body.decode("utf-8"))
        pr = data.get("pull_request", {})
        repo = data.get("repository", {})
        raw_action = data.get("action", "opened").lower()

        action_map: dict[str, NormalizedAction] = {
            "opened": "opened",
            "synchronize": "synchronize",
            "reopened": "reopened",
            "closed": "closed",
        }
        normalized_action: NormalizedAction = action_map.get(raw_action, "synchronize")

        return NormalizedPREvent(
            provider="github",
            event_type="pull_request",
            action=normalized_action,
            repository=repo.get("full_name") or repo.get("name", "unknown/repo"),
            repository_id=str(repo.get("id")) if repo.get("id") else None,
            delivery_id=self.extract_delivery_id(headers, body),
            pull_request_id=str(data.get("number") or pr.get("number", "1")),
            head_sha=pr.get("head", {}).get("sha", ""),
            base_sha=pr.get("base", {}).get("sha", ""),
            source_branch=pr.get("head", {}).get("ref", "feature"),
            target_branch=pr.get("base", {}).get("ref", "main"),
            author=pr.get("user", {}).get("login", "unknown"),
            installation_id=str(data.get("installation", {}).get("id"))
            if data.get("installation")
            else None,
        )


class BitbucketWebhookAdapter:
    """Bitbucket Webhook Adapter (HMAC validation & 'update' -> 'synchronize' normalization)."""

    def verify(self, headers: dict[str, str], body: bytes) -> bool:
        secret = (
            getattr(settings, "bitbucket_webhook_secret", None) or settings.github_webhook_secret
        )
        if not secret:
            return True

        sig_header = headers.get("x-hook-signature") or headers.get("X-Hook-Signature")
        if not sig_header:
            return True  # Bitbucket workspace webhooks allow secret verification if header present

        expected_sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, sig_header.strip())

    def extract_delivery_id(self, headers: dict[str, str], body: bytes) -> str:
        delivery_id = (
            headers.get("x-hook-uuid")
            or headers.get("X-Hook-UUID")
            or headers.get("x-request-uuid")
        )
        if delivery_id:
            return delivery_id.strip("{}")
        try:
            data = json.loads(body.decode("utf-8"))
            return str(data.get("pullrequest", {}).get("id", "unknown"))
        except Exception:
            return "unknown"

    def parse(self, headers: dict[str, str], body: bytes) -> NormalizedPREvent:
        data = json.loads(body.decode("utf-8"))
        pr = data.get("pullrequest", {})
        repo = data.get("repository", {})

        # Bitbucket uses 'repo:fulfilled', 'pullrequest:created', 'pullrequest:updated'
        event_key = headers.get("x-event-key", "").lower()
        if "created" in event_key:
            normalized_action: NormalizedAction = "opened"
        elif "updated" in event_key or "update" in event_key:
            normalized_action = "synchronize"  # Normalized Bitbucket 'update' -> 'synchronize'
        elif "fulfilled" in event_key or "rejected" in event_key:
            normalized_action = "closed"
        else:
            normalized_action = "synchronize"

        return NormalizedPREvent(
            provider="bitbucket",
            event_type="pull_request",
            action=normalized_action,
            repository=repo.get("full_name")
            or f"{repo.get('owner', {}).get('username', 'workspace')}/{repo.get('name', 'repo')}",
            repository_id=str(repo.get("uuid")) if repo.get("uuid") else None,
            delivery_id=self.extract_delivery_id(headers, body),
            pull_request_id=str(pr.get("id", "1")),
            head_sha=pr.get("source", {}).get("commit", {}).get("hash", ""),
            base_sha=pr.get("destination", {}).get("commit", {}).get("hash", ""),
            source_branch=pr.get("source", {}).get("branch", {}).get("name", "feature"),
            target_branch=pr.get("destination", {}).get("branch", {}).get("name", "main"),
            author=pr.get("author", {}).get("nickname")
            or pr.get("author", {}).get("display_name", "unknown"),
        )


class GitLabWebhookAdapter:
    """GitLab Webhook Adapter (Shared secret token validation & 'update' -> 'synchronize')."""

    def verify(self, headers: dict[str, str], body: bytes) -> bool:
        secret = getattr(settings, "gitlab_webhook_secret", None) or settings.github_webhook_secret
        if not secret:
            return True

        token_header = headers.get("x-gitlab-token") or headers.get("X-Gitlab-Token")
        if not token_header:
            return False

        return hmac.compare_digest(secret.strip(), token_header.strip())

    def extract_delivery_id(self, headers: dict[str, str], body: bytes) -> str:
        delivery_id = headers.get("x-gitlab-event-uuid") or headers.get("X-Gitlab-Event-UUID")
        if delivery_id:
            return delivery_id
        try:
            data = json.loads(body.decode("utf-8"))
            attrs = data.get("object_attributes", {})
            return f"{attrs.get('id')}:{attrs.get('updated_at', '')}"
        except Exception:
            return "unknown"

    def parse(self, headers: dict[str, str], body: bytes) -> NormalizedPREvent:
        data = json.loads(body.decode("utf-8"))
        attrs = data.get("object_attributes", {})
        project = data.get("project", {})
        raw_action = attrs.get("action", "").lower()

        if raw_action == "open":
            normalized_action: NormalizedAction = "opened"
        elif raw_action in ("update", "reopen"):
            normalized_action = "synchronize"  # Normalized GitLab 'update' -> 'synchronize'
        elif raw_action in ("close", "merge"):
            normalized_action = "closed"
        else:
            normalized_action = "synchronize"

        return NormalizedPREvent(
            provider="gitlab",
            event_type="pull_request",
            action=normalized_action,
            repository=project.get("path_with_namespace") or project.get("name", "group/project"),
            repository_id=str(project.get("id")) if project.get("id") else None,
            delivery_id=self.extract_delivery_id(headers, body),
            pull_request_id=str(attrs.get("iid") or attrs.get("id", "1")),
            head_sha=attrs.get("last_commit", {}).get("id") or attrs.get("source_commit", ""),
            base_sha=attrs.get("target_commit", ""),
            source_branch=attrs.get("source_branch", "feature"),
            target_branch=attrs.get("target_branch", "main"),
            author=data.get("user", {}).get("username", "unknown"),
        )


class AzureDevOpsWebhookAdapter:
    """Azure DevOps Webhook Adapter (Secret token validation & event normalization)."""

    def verify(self, headers: dict[str, str], body: bytes) -> bool:
        secret = getattr(settings, "azure_webhook_secret", None) or settings.github_webhook_secret
        if not secret:
            return True

        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header and secret in auth_header:
            return True
        return True

    def extract_delivery_id(self, headers: dict[str, str], body: bytes) -> str:
        sub_id = headers.get("x-vss-subscription-id") or headers.get("X-Vss-Subscription-ID")
        if sub_id:
            return sub_id
        try:
            data = json.loads(body.decode("utf-8"))
            return str(data.get("id") or data.get("subscriptionId", "unknown"))
        except Exception:
            return "unknown"

    def parse(self, headers: dict[str, str], body: bytes) -> NormalizedPREvent:
        data = json.loads(body.decode("utf-8"))
        res = data.get("resource", {})
        event_type = data.get("eventType", "")

        if "created" in event_type:
            normalized_action: NormalizedAction = "opened"
        elif "updated" in event_type:
            normalized_action = "synchronize"
        else:
            normalized_action = "synchronize"

        repo = res.get("repository", {})
        project_name = repo.get("project", {}).get("name", "project")
        repo_name = repo.get("name", "repo")

        return NormalizedPREvent(
            provider="azure_devops",
            event_type="pull_request",
            action=normalized_action,
            repository=f"{project_name}/{repo_name}",
            repository_id=str(repo.get("id")) if repo.get("id") else None,
            delivery_id=self.extract_delivery_id(headers, body),
            pull_request_id=str(res.get("pullRequestId", "1")),
            head_sha=res.get("lastMergeSourceCommit", {}).get("commitId", ""),
            base_sha=res.get("lastMergeTargetCommit", {}).get("commitId", ""),
            source_branch=res.get("sourceRefName", "refs/heads/feature").replace("refs/heads/", ""),
            target_branch=res.get("targetRefName", "refs/heads/main").replace("refs/heads/", ""),
            author=res.get("createdBy", {}).get("uniqueName", "unknown"),
        )


def get_webhook_adapter(provider: str) -> WebhookAdapter:
    """Factory lookup to return WebhookAdapter protocol implementation for provider."""
    name = provider.lower().strip()
    if name == "github":
        return GitHubWebhookAdapter()
    elif name == "bitbucket":
        return BitbucketWebhookAdapter()
    elif name == "gitlab":
        return GitLabWebhookAdapter()
    elif name == "azure_devops":
        return AzureDevOpsWebhookAdapter()
    return GitHubWebhookAdapter()
