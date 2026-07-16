"""TestPilot AI — Repository Pydantic Schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, HttpUrl

from app.schemas.common import BaseSchema


class IndexStatus(str, Enum):
    """Repository indexing status."""
    PENDING = "pending"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class RepositoryConnectRequest(BaseSchema):
    """Request body to connect a new GitHub repository."""

    full_name: str = Field(
        ...,
        description="GitHub repository full name (e.g., 'owner/repo')",
        examples=["octocat/Hello-World"],
    )
    github_app_installation_id: str | None = Field(
        default=None,
        description="GitHub App installation ID (for private repos)",
    )


class RepositoryIndexRequest(BaseSchema):
    """Request to trigger repository indexing."""

    force_reindex: bool = Field(
        default=False,
        description="Force re-indexing even if already indexed",
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
    """Detailed repository response including metrics."""

    total_pull_requests: int = 0
    open_pull_requests: int = 0
    recent_risk_scores: list[float] = Field(default_factory=list)
    top_risk_modules: list[str] = Field(default_factory=list)


class RepositoryHealthResponse(BaseSchema):
    """Repository health score breakdown."""

    overall_score: float
    coverage_score: float
    test_quality_score: float
    risk_score: float
    activity_score: float
    factors: list[str]
