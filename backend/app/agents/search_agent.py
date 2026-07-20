"""TestPilot AI — Search Agent.

Performs hybrid semantic + structural code search to retrieve relevant
context for the changed code. Uses Qdrant for vector search and the
dependency graph for structural retrieval.

This context is used by the Test Generator Agent to generate
style-consistent, API-accurate tests.
"""

from __future__ import annotations

import time
from typing import Any

from app.agents.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


def search_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: retrieve relevant code context via hybrid search.

    Searches the Qdrant vector store for semantically similar code snippets
    and combines with dependency graph structural retrieval.

    Args:
        state: Current AgentState with changed_nodes and affected_modules.

    Returns:
        Partial state with retrieved_context.
    """
    start_time = time.monotonic()
    logger.info("Search agent started", pr_id=state.get("pr_id"))

    try:
        from app.core.config import get_settings
        from app.utils.qdrant_client import get_qdrant_client

        settings = get_settings()

        changed_nodes = state.get("changed_nodes", [])
        retrieved_context = []

        if changed_nodes:
            qdrant = get_qdrant_client()

            # Build search queries from changed function/class names
            for node in changed_nodes[:10]:  # Limit to top 10 nodes
                query = f"{node['type']} {node['name']} in {node['file_path']}"
                try:
                    results = qdrant.search(  # type: ignore[attr-defined]
                        collection_name=settings.qdrant_collection_repository_chunks,
                        query_text=query,
                        limit=3,
                        query_filter={
                            "must": [
                                {"key": "repository_id", "match": {"value": state["repository_id"]}}
                            ]
                        },
                    )
                    for result in results:
                        retrieved_context.append(
                            {
                                "score": result.score,
                                "content": result.payload.get("content", ""),
                                "file_path": result.payload.get("file_path", ""),
                                "language": result.payload.get("language", ""),
                                "function_name": result.payload.get("function_name"),
                            }
                        )
                except Exception as search_err:
                    logger.warning(
                        "Qdrant search failed for node", node=node["name"], error=str(search_err)
                    )

        duration = time.monotonic() - start_time
        logger.info(
            "Search agent completed",
            results=len(retrieved_context),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("search_agent")

        return {
            "retrieved_context": retrieved_context,
            "completed_agents": completed,
            "current_agent": "search_agent",
        }

    except Exception as e:
        logger.exception("Search agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"search_agent: {e}")
        return {"errors": errors, "retrieved_context": []}
