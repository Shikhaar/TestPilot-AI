"""TestPilot AI — Bug History ORM Model.

This model powers the "Learning from Historical Bugs" feature.
Every time a bug is identified (from failed PRs, incidents, etc.),
it is stored here with an embedding reference for future similarity search.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class BugHistory(Base, UUIDMixin, TimestampMixin):
    """Historical record of bugs associated with code changes.

    When a new PR arrives, the system queries this table via embedding
    similarity to determine: "Has a similar change caused a bug before?"

    Attributes:
        repository_id: FK to the parent repository.
        commit_sha: The commit SHA where the bug was introduced.
        pr_number: GitHub PR number (if associated with a PR).
        module_path: The module/file path where the bug occurred.
        function_name: Specific function (if known).
        bug_type: Category: 'regression' | 'null_pointer' | 'race_condition' | etc.
        description: Human-readable description of the bug.
        root_cause: Root cause analysis.
        fix_commit_sha: SHA of the commit that fixed this bug.
        severity: 'low' | 'medium' | 'high' | 'critical'.
        qdrant_embedding_id: ID of the embedding stored in Qdrant.
        is_production_incident: Whether this was a production incident.
        incident_date: Date of the incident.
        tags: JSON list of tags for categorization.
    """

    __tablename__ = "bug_history"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    pr_number: Mapped[int | None] = mapped_column(String(10), nullable=True)
    module_path: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    function_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bug_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_commit_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False, index=True)
    qdrant_embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_production_incident: Mapped[bool] = mapped_column(String(5), default=False, nullable=False)
    incident_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list[str]

    # Relationships
    repository: Mapped[Repository] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Repository",
        back_populates="bug_history",
    )

    def __repr__(self) -> str:
        return f"<BugHistory id={self.id} type={self.bug_type} severity={self.severity}>"
