"""
TestPilot AI — Impact Analyzer Service.

Queries the dependency graph of a repository to compute the impact radius
and find downstream files, services, and APIs affected by code changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency_graph import DependencyEdge
from app.services.dependency_graph_builder import DependencyGraphBuilder


class ImpactAnalyzer:
    """Service to compute downstream impact of modified codebase files."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analyze_impact(
        self,
        repository_id: str,
        repo_path: Path,
        changed_files: list[str],
        depth: int = 5,
    ) -> dict[str, Any]:
        """Determine downstream affected files from code changes.

        Args:
            repository_id: The repository UUID.
            repo_path: The local repository root path.
            changed_files: List of file paths relative to repo root.
            depth: Traversal depth limit.

        Returns:
            Dictionary containing affected modules, APIs, and impact statistics.
        """
        # Load edges from database
        result = await self.db.execute(
            select(DependencyEdge).where(DependencyEdge.repository_id == repository_id)
        )
        edges = result.scalars().all()

        edge_records = [
            {
                "source_node": e.source_node,
                "target_node": e.target_node,
                "edge_type": e.edge_type,
            }
            for e in edges
        ]

        # Build graph and traverse
        builder = DependencyGraphBuilder.from_edge_records(edge_records, repo_path)
        affected_map = builder.get_affected_by_changes(changed_files, depth=depth)

        all_affected: set[str] = set()
        for dependents in affected_map.values():
            all_affected.update(dependents)

        affected_modules = list(all_affected)

        # Categorize
        affected_services = [p for p in affected_modules if "service" in p.lower()]
        affected_apis = [
            p
            for p in affected_modules
            if any(k in p.lower() for k in ("api", "router", "route", "controller", "endpoint"))
        ]

        # Determine overall level
        impact_radius = len(affected_modules)
        if impact_radius == 0:
            level = "isolated"
        elif impact_radius < 5:
            level = "moderate"
        else:
            level = "widespread"

        return {
            "affected_modules": affected_modules,
            "affected_services": affected_services,
            "affected_apis": affected_apis,
            "impact_radius": impact_radius,
            "impact_level": level,
            "per_file": {k: list(v) for k, v in affected_map.items()},
        }
