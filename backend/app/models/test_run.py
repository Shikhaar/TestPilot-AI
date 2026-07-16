"""TestPilot AI — Test Run ORM Model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.test_result import TestResult


class TestRun(Base, UUIDMixin, TimestampMixin):
    """Represents a single test suite execution run.

    Attributes:
        pull_request_id: FK to the triggering pull request.
        repository_id: FK to the parent repository.
        runner: Test runner used: 'pytest' | 'jest' | 'go_test' | 'junit'.
        status: 'pending' | 'running' | 'passed' | 'failed' | 'error'.
        started_at: ISO timestamp when run started.
        finished_at: ISO timestamp when run finished.
        duration_seconds: Total run duration.
        total_tests: Total test count.
        passed_tests: Number of passing tests.
        failed_tests: Number of failing tests.
        skipped_tests: Number of skipped tests.
        error_tests: Number of tests with errors.
        coverage_percentage: Overall coverage after this run.
        coverage_report: JSON coverage report data.
        command: Exact command used to run tests.
        working_directory: Directory where tests were run.
        logs: Full test output logs.
        failure_summary: AI-generated failure summary.
    """

    __tablename__ = "test_runs"

    pull_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    runner: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Results
    total_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_tests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coverage_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    coverage_report: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Execution context
    command: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_directory: Mapped[str | None] = mapped_column(Text, nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # AI-generated

    # Relationships
    pull_request: Mapped["PullRequest"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "PullRequest",
        back_populates="test_runs",
    )
    results: Mapped[list["TestResult"]] = relationship(
        "TestResult",
        back_populates="test_run",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<TestRun id={self.id} runner={self.runner} status={self.status}>"
