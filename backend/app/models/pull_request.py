"""TestPilot AI — Pull Request ORM Model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.agent_run import AgentRun
    from app.models.generated_test import GeneratedTest
    from app.models.repository import Repository
    from app.models.review_comment import ReviewComment
    from app.models.test_run import TestRun


class PullRequest(Base, UUIDMixin, TimestampMixin):
    """Represents a GitHub Pull Request analyzed by TestPilot AI.

    Attributes:
        repository_id: FK to the parent repository.
        pr_number: GitHub PR number.
        github_pr_id: GitHub's numeric PR ID.
        title: PR title.
        description: PR body/description.
        state: 'open' | 'closed' | 'merged'.
        author: GitHub username of PR author.
        base_branch: Target branch (e.g., 'main').
        head_branch: Source branch.
        head_sha: HEAD commit SHA.
        base_sha: Base commit SHA.

        # Analysis
        analysis_status: 'pending' | 'running' | 'completed' | 'failed'.
        risk_level: 'low' | 'medium' | 'high' | 'critical'.
        risk_score: Numeric risk score (0.0 - 10.0).
        risk_factors: JSON-serialized list of risk factor strings.
        affected_modules: JSON list of affected module paths.

        # Coverage
        coverage_before: Coverage percentage before this PR.
        coverage_after: Coverage percentage after this PR.
        coverage_delta: Change in coverage percentage.

        # Diff stats
        files_changed: Number of files changed.
        lines_added: Total lines added.
        lines_removed: Total lines removed.

        # GitHub
        github_review_id: ID of the review posted to GitHub.
        github_check_run_id: ID of the GitHub check run.
    """

    __tablename__ = "pull_requests"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    github_pr_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    base_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    head_branch: Mapped[str] = mapped_column(String(255), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    base_sha: Mapped[str] = mapped_column(String(40), nullable=False)

    # Analysis state
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    analysis_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Risk
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_factors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    affected_modules: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Coverage
    coverage_before: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_after: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_delta: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Diff stats
    files_changed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lines_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # GitHub review artifacts
    github_review_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    github_check_run_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    repository: Mapped[Repository] = relationship("Repository", back_populates="pull_requests")
    generated_tests: Mapped[list[GeneratedTest]] = relationship(
        "GeneratedTest", back_populates="pull_request", cascade="all, delete-orphan"
    )
    test_runs: Mapped[list[TestRun]] = relationship(
        "TestRun", back_populates="pull_request", cascade="all, delete-orphan"
    )
    review_comments: Mapped[list[ReviewComment]] = relationship(
        "ReviewComment", back_populates="pull_request", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list[AgentRun]] = relationship(
        "AgentRun", back_populates="pull_request", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PullRequest id={self.id} pr_number={self.pr_number} state={self.state}>"
