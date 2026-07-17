"""TestPilot AI — Generated Test ORM Model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class GeneratedTest(Base, UUIDMixin, TimestampMixin):
    """Represents an AI-generated test case.

    Attributes:
        pull_request_id: FK to the PR that triggered generation.
        repository_id: FK to the parent repository.
        file_path: The target file this test covers.
        test_file_path: Path where the test file should be written.
        function_name: The specific function under test.
        class_name: The specific class under test.
        content: Full test file content.
        language: Programming language.
        test_framework: Test framework: 'pytest' | 'jest' | 'junit' | 'go_test'.
        test_type: Type: 'unit' | 'integration' | 'edge_case' | 'negative' | 'property'.
        status: 'generated' | 'applied' | 'passed' | 'failed' | 'skipped'.
        run_result: JSON result from last test execution.
        model_used: LLM model that generated this test.
        generation_prompt_tokens: Tokens used in generation prompt.
        generation_completion_tokens: Tokens in the completion.
    """

    __tablename__ = "generated_tests"

    pull_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    test_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    function_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    class_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    test_framework: Mapped[str] = mapped_column(String(50), default="pytest", nullable=False)
    test_type: Mapped[str] = mapped_column(String(50), default="unit", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="generated", nullable=False, index=True)
    run_result: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # AI metadata
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation_prompt_tokens: Mapped[int | None] = mapped_column(String(10), nullable=True)
    generation_completion_tokens: Mapped[int | None] = mapped_column(String(10), nullable=True)

    # Relationships
    pull_request: Mapped[PullRequest] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "PullRequest",
        back_populates="generated_tests",
    )

    def __repr__(self) -> str:
        return f"<GeneratedTest id={self.id} type={self.test_type} status={self.status}>"
