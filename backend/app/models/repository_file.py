"""TestPilot AI — Repository File ORM Model."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class RepositoryFile(Base, UUIDMixin, TimestampMixin):
    """Represents a source file within a repository.

    After indexing, each file's AST is parsed and code symbols extracted.
    This record tracks what was found and when it was last parsed.

    Attributes:
        repository_id: FK to the parent repository.
        path: Relative file path within the repository.
        language: Detected programming language.
        size_bytes: File size in bytes.
        ast_hash: SHA256 of the file content at parse time.
        last_parsed_at: Timestamp of last AST parse.
        is_test_file: Whether this file is a test file.
        functions: JSON list of extracted function names.
        classes: JSON list of extracted class names.
        imports: JSON list of extracted import paths.
        exports: JSON list of exported symbols.
        routes: JSON list of extracted API routes.
        qdrant_chunk_ids: JSON list of Qdrant vector IDs for this file's chunks.
        line_count: Total number of lines.
        complexity_score: Cyclomatic complexity score.
    """

    __tablename__ = "repository_files"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    path: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ast_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_parsed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_test_file: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    # Extracted code symbols (stored as JSON strings)
    functions: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON list[str]
    classes: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON list[str]
    imports: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON list[str]
    exports: Mapped[str | None] = mapped_column(Text, nullable=True)      # JSON list[str]
    routes: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON list[dict]
    qdrant_chunk_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list[str]

    # Metrics
    line_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    complexity_score: Mapped[float | None] = mapped_column(Integer, nullable=True)

    # Relationships
    repository: Mapped["Repository"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Repository",
        back_populates="files",
    )

    def __repr__(self) -> str:
        return f"<RepositoryFile id={self.id} path={self.path}>"
