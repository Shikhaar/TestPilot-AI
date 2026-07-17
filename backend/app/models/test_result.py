"""TestPilot AI — Test Result ORM Model."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class TestResult(Base, UUIDMixin, TimestampMixin):
    """Represents a single test case result within a test run.

    Attributes:
        test_run_id: FK to the parent test run.
        test_name: Full qualified test name.
        test_file: Source file containing the test.
        test_class: Test class name (if applicable).
        status: 'passed' | 'failed' | 'skipped' | 'error'.
        duration_seconds: Test execution duration.
        failure_message: Failure message if status is 'failed'.
        failure_type: Exception type (e.g., 'AssertionError').
        stack_trace: Full stack trace.
        stdout: Captured standard output.
        stderr: Captured standard error.
        root_cause: AI-determined root cause of failure.
        suggested_fix: AI-suggested fix for the failure.
        confidence_score: AI confidence in the root cause analysis.
    """

    __tablename__ = "test_results"

    test_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    test_name: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    test_file: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_class: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Failure details
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stack_trace: Mapped[str | None] = mapped_column(Text, nullable=True)
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI analysis
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    test_run: Mapped[TestRun] = relationship("TestRun", back_populates="results")  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<TestResult id={self.id} test_name={self.test_name[:50]} status={self.status}>"
