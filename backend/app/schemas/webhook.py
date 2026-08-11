"""TestPilot AI — Webhook Schema Definitions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

NormalizedAction = Literal["opened", "synchronize", "reopened", "closed"]


class NormalizedPREvent(BaseModel):
    """Normalized Pull Request event schema across all VCS providers."""

    provider: str = Field(description="VCS provider: github | bitbucket | gitlab | azure_devops")
    event_type: str = Field(
        default="pull_request",
        description="Extensible event type; pull_request is primary supported in Phase 1",
    )
    action: NormalizedAction = Field(
        description="Provider-normalized action: opened | synchronize | reopened | closed"
    )
    repository: str = Field(description="Full repository identifier e.g. owner/repo")
    repository_id: str | None = Field(
        default=None, description="Provider-specific immutable repository ID"
    )
    delivery_id: str = Field(description="Unique event/delivery ID assigned by VCS provider")
    pull_request_id: str = Field(description="Pull request number or ID e.g. 42 or PR-10")
    head_sha: str = Field(description="Commit SHA of the pull request head branch")
    base_sha: str = Field(description="Commit SHA of the target base branch")
    source_branch: str = Field(description="Name of the source feature branch")
    target_branch: str = Field(description="Name of the target base branch e.g. main/master")
    author: str = Field(description="Username of the pull request author")
    installation_id: str | None = Field(
        default=None, description="GitHub App or OAuth installation/organization ID"
    )
