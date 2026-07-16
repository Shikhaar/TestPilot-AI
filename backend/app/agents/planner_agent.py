"""TestPilot AI — Planner Agent.

The supervisor agent that initializes the pipeline state and
validates pre-conditions before the main agent sequence begins.
"""

from __future__ import annotations

import time
from typing import Any

from app.agents.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def planner_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: initialize and validate the analysis pipeline.

    Checks that all required inputs are present and sets up initial
    control flow state before handing off to the Diff Agent.

    Args:
        state: Initial AgentState.

    Returns:
        Updated state with control flow fields initialized.
    """
    logger.info(
        "Planner agent started",
        pr_id=state.get("pr_id"),
        repo=state.get("repo_full_name"),
        pr_number=state.get("pr_number"),
    )

    required_fields = ["pr_id", "repository_id", "repo_full_name", "pr_number", "head_sha"]
    missing = [f for f in required_fields if not state.get(f)]

    if missing:
        logger.error("Planner agent: missing required fields", missing=missing)
        return {
            "errors": [f"Missing required fields: {', '.join(missing)}"],
            "should_stop": True,
            "completed_agents": ["planner_agent"],
            "current_agent": "planner_agent",
        }

    logger.info("Planner agent: all pre-conditions met, starting pipeline")

    return {
        "errors": [],
        "retry_count": 0,
        "should_stop": False,
        "completed_agents": ["planner_agent"],
        "current_agent": "planner_agent",
    }


"""TestPilot AI — Documentation Agent (stub)."""


def documentation_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: update documentation based on code changes.

    Currently a stub — generates documentation update suggestions
    based on changed API routes and function signatures.

    Args:
        state: Current AgentState.

    Returns:
        Partial state with documentation_updates.
    """
    logger.info("Documentation agent started", pr_id=state.get("pr_id"))

    # Identify routes that changed
    changed_routes = [
        node for node in state.get("changed_nodes", [])
        if node["type"] == "route"
    ]

    doc_updates = []
    for route in changed_routes:
        doc_updates.append({
            "type": "api_route_change",
            "route": route["name"],
            "file": route["file_path"],
            "suggestion": f"Update API documentation for {route['name']}",
        })

    completed = list(state.get("completed_agents", []))
    completed.append("documentation_agent")

    return {
        "documentation_updates": doc_updates,
        "completed_agents": completed,
        "current_agent": "documentation_agent",
    }
