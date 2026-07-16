"""TestPilot AI — AI Log ORM Model."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class AILog(Base, UUIDMixin, TimestampMixin):
    """Logs every LLM API call for cost tracking, auditing, and debugging.

    Attributes:
        agent_name: Name of the LangGraph agent that made the call.
        model: LLM model used (e.g., 'gpt-4o-mini').
        operation: Operation type: 'completion' | 'embedding' | 'structured_output'.
        prompt_tokens: Tokens in the prompt.
        completion_tokens: Tokens in the completion.
        total_tokens: Total tokens used.
        latency_ms: Request latency in milliseconds.
        cost_usd: Estimated cost in USD.
        success: Whether the call succeeded.
        error_message: Error message if call failed.
        pr_id: Optional FK to the associated pull request.
        repository_id: Optional FK to the associated repository.
    """

    __tablename__ = "ai_logs"

    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(50), default="completion", nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    success: Mapped[bool] = mapped_column(String(5), default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    pr_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="SET NULL"), nullable=True, index=True
    )
    repository_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<AILog id={self.id} agent={self.agent_name} model={self.model} tokens={self.total_tokens}>"
