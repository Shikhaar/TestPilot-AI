"""TestPilot AI — Impact Agent.

Traverses the dependency graph to determine which modules, services,
APIs, and downstream dependencies are affected by the PR changes.

Uses the DependencyGraphBuilder for BFS traversal from changed nodes.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.agents.state import AgentState
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.dependency_graph_builder import DependencyGraphBuilder

logger = get_logger(__name__)
settings = get_settings()


def impact_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: determine impact radius of PR changes.

    Takes the dependency graph edges and changed files, then performs
    BFS traversal to find all transitively affected modules.

    Args:
        state: Current AgentState with dependency_graph_edges and changed_files.

    Returns:
        Partial state with affected_modules, affected_services, affected_apis.
    """
    start_time = time.monotonic()
    logger.info("Impact agent started", pr_id=state.get("pr_id"))

    try:
        repo_root = settings.repo_storage_path / state["repository_id"]

        # Reconstruct graph from edge records
        builder = DependencyGraphBuilder.from_edge_records(
            records=state.get("dependency_graph_edges", []),
            repo_root=Path(repo_root),
        )

        changed_file_paths = [f["path"] for f in state.get("changed_files", [])]

        # Find all affected modules via BFS
        affected_map = builder.get_affected_by_changes(changed_file_paths, depth=5)

        all_affected: set[str] = set()
        for dependents in affected_map.values():
            all_affected.update(dependents)

        # Categorize affected modules
        affected_services = [p for p in all_affected if "service" in p.lower()]
        affected_apis = [p for p in all_affected if any(
            k in p.lower() for k in ("api", "router", "route", "controller", "endpoint", "view")
        )]

        duration = time.monotonic() - start_time
        logger.info(
            "Impact agent completed",
            affected_modules=len(all_affected),
            affected_services=len(affected_services),
            affected_apis=len(affected_apis),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("impact_agent")

        return {
            "affected_modules": list(all_affected),
            "affected_services": affected_services,
            "affected_apis": affected_apis,
            "completed_agents": completed,
            "current_agent": "impact_agent",
        }

    except Exception as e:
        logger.exception("Impact agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"impact_agent: {e}")
        return {
            "errors": errors,
            "affected_modules": [],
            "affected_services": [],
            "affected_apis": [],
        }
