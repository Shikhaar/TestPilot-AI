"""TestPilot AI — Repository ORM Model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.pull_request import PullRequest
    from app.models.repository_file import RepositoryFile
    from app.models.dependency_graph import DependencyEdge
    from app.models.bug_history import BugHistory


class Repository(Base, UUIDMixin, TimestampMixin):
    """Represents a connected GitHub repository.

    A repository is connected by a user and indexed by TestPilot AI.
    After indexing, its files, AST, and dependency graph are stored.

    Attributes:
        owner_id: FK to the user who connected this repository.
        github_repo_id: GitHub's numeric repository ID.
        full_name: GitHub full name, e.g., 'owner/repo'.
        name: Repository name.
        owner_login: GitHub owner login.
        description: Repository description.
        clone_url: HTTPS URL for cloning.
        ssh_url: SSH URL for cloning.
        default_branch: Default branch (usually 'main' or 'master').
        language: Primary programming language.
        is_private: Whether the repository is private.
        is_indexed: Whether the repository has been fully indexed.
        indexed_at: Timestamp of last successful indexing.
        index_status: 'pending' | 'indexing' | 'indexed' | 'failed'.
        total_files: Total files indexed.
        total_functions: Total functions extracted.
        total_classes: Total classes extracted.
        health_score: Overall repository health score (0-100).
        coverage_percentage: Last known test coverage percentage.
        local_path: Local path where repo is cloned.
        github_app_installation_id: GitHub App installation ID.
    """

    __tablename__ = "repositories"

    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    github_repo_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_login: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    clone_url: Mapped[str] = mapped_column(Text, nullable=False)
    ssh_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main", nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Indexing status
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    indexed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    index_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    index_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Metrics
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_functions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_classes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    health_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    coverage_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Storage
    local_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_app_installation_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="repositories")
    pull_requests: Mapped[list["PullRequest"]] = relationship(
        "PullRequest", back_populates="repository", cascade="all, delete-orphan"
    )
    files: Mapped[list["RepositoryFile"]] = relationship(
        "RepositoryFile", back_populates="repository", cascade="all, delete-orphan"
    )
    dependency_edges: Mapped[list["DependencyEdge"]] = relationship(
        "DependencyEdge", back_populates="repository", cascade="all, delete-orphan"
    )
    bug_history: Mapped[list["BugHistory"]] = relationship(
        "BugHistory", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository id={self.id} full_name={self.full_name}>"
