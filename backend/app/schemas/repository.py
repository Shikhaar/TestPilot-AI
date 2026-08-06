"""TestPilot AI — Repository Pydantic Schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field, field_validator

from app.schemas.common import BaseSchema


class IndexStatus(StrEnum):
    """Repository indexing status."""

    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class RepositoryConnectRequest(BaseSchema):
    """Request body to connect a new VCS repository."""

    full_name: str = Field(
        ...,
        description="Repository full name or Git URL (e.g., 'owner/repo' or 'https://gitlab.com/group/repo')",
        examples=["octocat/Hello-World"],
    )
    provider: str = Field(
        default="github",
        description="VCS provider: github | bitbucket | gitlab | azure_devops | custom_git",
    )
    access_token: str | None = Field(
        default=None,
        description="Personal Access Token or App Password for private Bitbucket/GitLab repos",
    )
    github_app_installation_id: str | None = Field(
        default=None,
        description="GitHub App installation ID (for private repos)",
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Repository name or URL cannot be empty")
        return v


class RepositoryIndexRequest(BaseSchema):
    """Request to trigger repository indexing."""

    force_reindex: bool = Field(
        default=False,
        description="Force re-indexing even if already indexed",
    )
    branch: str | None = Field(
        default=None,
        description="Specific git branch to clone and index (defaults to repo default_branch)",
    )


class RepositoryResponse(BaseSchema):
    """Response schema for a repository."""

    id: str
    full_name: str
    name: str
    owner_login: str
    description: str | None
    clone_url: str
    default_branch: str
    language: str | None
    is_private: bool
    is_indexed: bool
    indexed_at: str | None
    index_status: str
    total_files: int
    total_functions: int
    total_classes: int
    health_score: float
    coverage_percentage: float | None
    created_at: datetime


class RepositoryDetailResponse(RepositoryResponse):
    """Detailed repository response including real AST metrics and architecture summary."""

    total_pull_requests: int = 0
    open_pull_requests: int = 0
    recent_risk_scores: list[float] = Field(default_factory=list)
    top_risk_modules: list[str] = Field(default_factory=list)

    routes_nodes: int = 0
    services_nodes: int = 0
    repositories_nodes: int = 0
    architecture_summary: str = ""
    ai_summary: str = ""
    test_framework: str = "pytest"


class RepositoryHealthResponse(BaseSchema):
    """Repository health score breakdown."""

    overall_score: float
    coverage_score: float
    test_quality_score: float
    risk_score: float
    activity_score: float
    factors: list[str]
