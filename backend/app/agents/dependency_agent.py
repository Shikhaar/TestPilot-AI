"""TestPilot AI — Dependency Agent.

Loads the pre-built dependency graph for the repository from the database
(or rebuilds it from AST results if not cached). Makes the graph available
to downstream agents for impact analysis.
"""

from __future__ import annotations

import time
from typing import Any

from app.agents.state import AgentState
from app.core.logging import get_logger
from app.database.session import get_session

logger = get_logger(__name__)


def dependency_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: load/rebuild the repository dependency graph.

    Checks if the dependency graph is already stored in the database.
    If yes, loads it. If not, triggers a rebuild from stored AST results.

    Args:
        state: Current AgentState.

    Returns:
        Partial state update with dependency_graph_edges.
    """
    start_time = time.monotonic()
    logger.info("Dependency agent started", repo_id=state.get("repository_id"))

    try:
        import asyncio

        edges = asyncio.run(_load_dependency_edges(state["repository_id"]))

        duration = time.monotonic() - start_time
        logger.info(
            "Dependency agent completed",
            edges=len(edges),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("dependency_agent")

        return {
            "dependency_graph_edges": edges,
            "completed_agents": completed,
            "current_agent": "dependency_agent",
        }

    except Exception as e:
        logger.exception("Dependency agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"dependency_agent: {e}")
        return {"errors": errors, "dependency_graph_edges": []}


async def _load_dependency_edges(repository_id: str) -> list[dict[str, str]]:
    """Load dependency graph edges from the database."""
    from sqlalchemy import select

    from app.models.dependency_graph import DependencyEdge

    async with get_session() as db:
        result = await db.execute(
            select(DependencyEdge).where(DependencyEdge.repository_id == repository_id)
        )
        edges = result.scalars().all()
        return [
            {
                "source_node": e.source_node,
                "target_node": e.target_node,
                "edge_type": e.edge_type,
            }
            for e in edges
        ]
