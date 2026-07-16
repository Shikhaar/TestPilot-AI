"""TestPilot AI — Dependency Graph Edge ORM Model."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin


class DependencyEdge(Base, UUIDMixin, TimestampMixin):
    """Represents a directed edge in the repository dependency graph.

    Each edge captures a dependency relationship between two code nodes
    (files, modules, classes, or functions). The graph is built from AST
    analysis of import statements and call expressions.

    Edge types:
        - 'imports': File A imports from File B
        - 'calls': Function A calls Function B
        - 'inherits': Class A inherits from Class B
        - 'uses': Module A uses Module B (indirect dependency)
        - 'tests': Test file A tests Module B

    Attributes:
        repository_id: FK to the parent repository.
        source_node: The dependent node (e.g., file path or qualified name).
        target_node: The dependency node.
        source_type: Type of the source node: 'file' | 'function' | 'class'.
        target_type: Type of the target node.
        edge_type: Nature of the dependency.
        line_number: Line number where the dependency appears.
        metadata_json: Additional metadata (e.g., alias, re-export).
    """

    __tablename__ = "dependency_graph"

    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_node: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    target_node: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(20), default="file", nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), default="file", nullable=False)
    edge_type: Mapped[str] = mapped_column(String(20), default="imports", nullable=False, index=True)
    line_number: Mapped[int | None] = mapped_column(String(10), nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON

    # Relationships
    repository: Mapped["Repository"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Repository",
        back_populates="dependency_edges",
    )

    def __repr__(self) -> str:
        return f"<DependencyEdge {self.source_node} --[{self.edge_type}]--> {self.target_node}>"
