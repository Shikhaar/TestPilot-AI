"""TestPilot AI — Commit ORM Model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class Commit(Base, UUIDMixin, TimestampMixin):
    """Represents a Git commit in a repository.

    Attributes:
        repository_id: FK to the parent repository.
        sha: Full commit SHA.
        short_sha: First 7 characters of the SHA.
        message: Commit message.
        author_name: Git author name.
        author_email: Git author email.
        author_github_username: GitHub username of the author.
        committed_at: ISO timestamp of the commit.
        parents: JSON list of parent SHAs.
    """

    __tablename__ = "commits"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sha: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    short_sha: Mapped[str] = mapped_column(String(7), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    author_name: Mapped[str] = mapped_column(String(255), nullable=False)
    author_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_github_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    committed_at: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    parents: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of SHAs

    def __repr__(self) -> str:
        return f"<Commit id={self.id} sha={self.short_sha}>"
