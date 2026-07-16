"""TestPilot AI — Agent Run ORM Model."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class AgentRun(Base, UUIDMixin, TimestampMixin):
    """Records the execution of a single LangGraph agent for a PR.

    Provides per-agent observability: input, output, duration, errors,
    and retry count. Enables debugging and performance profiling.

    Attributes:
        pull_request_id: FK to the triggering pull request.
        agent_name: Agent identifier (e.g., 'diff_agent').
        status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped'.
        started_at: ISO timestamp when the agent started.
        finished_at: ISO timestamp when the agent finished.
        duration_ms: Execution duration in milliseconds.
        input_data: JSON-serialized agent input state.
        output_data: JSON-serialized agent output.
        error_message: Error message if the agent failed.
        retry_count: Number of times this agent was retried.
        llm_calls: Number of LLM calls made by this agent.
        total_tokens: Total tokens consumed.
    """

    __tablename__ = "agent_runs"

    pull_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    pull_request: Mapped["PullRequest"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "PullRequest",
        back_populates="agent_runs",
    )

    def __repr__(self) -> str:
        return f"<AgentRun id={self.id} agent={self.agent_name} status={self.status}>"
