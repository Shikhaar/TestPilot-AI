"""
TestPilot AI — LangGraph Multi-Agent Pipeline Graph.

Assembles all agents into a directed LangGraph StateGraph.
The Planner Agent acts as a supervisor, deciding which agents to invoke.
Each agent node wraps a focused, single-responsibility agent function.

Pipeline flow:
    planner → diff_agent → dependency_agent → impact_agent
    → search_agent → test_discovery → test_generator
    → execution → failure_analysis → review → END

Conditional routing is used to skip agents when not needed
(e.g., skip execution if no tests were generated).
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from app.agents.state import AgentState
from app.core.logging import get_logger

logger = get_logger(__name__)


# ==============================================================================
# Import all agent node functions
# ==============================================================================

from app.agents.dependency_agent import dependency_agent_node
from app.agents.diff_agent import diff_agent_node
from app.agents.documentation_agent import documentation_agent_node
from app.agents.execution_agent import execution_agent_node
from app.agents.failure_analysis_agent import failure_analysis_agent_node
from app.agents.impact_agent import impact_agent_node
from app.agents.planner_agent import planner_agent_node
from app.agents.review_agent import review_agent_node
from app.agents.search_agent import search_agent_node
from app.agents.test_discovery_agent import test_discovery_agent_node
from app.agents.test_generator_agent import test_generator_agent_node

# ==============================================================================
# Conditional routing functions
# ==============================================================================


def should_continue_after_diff(
    state: AgentState,
) -> Literal["dependency_agent", "review_agent", END]:
    """Route after diff agent: stop early if no supported files changed."""
    if state.get("should_stop"):
        logger.info("Pipeline stopping early after diff agent")
        return END

    changed_nodes = state.get("changed_nodes", [])
    if not changed_nodes:
        logger.info("No code nodes changed, routing to review agent directly")
        return "review_agent"

    return "dependency_agent"


def should_run_execution(state: AgentState) -> Literal["execution_agent", "review_agent"]:
    """Route after test generation: skip execution if no tests generated."""
    generated = state.get("generated_tests", [])
    if not generated:
        logger.info("No tests generated, skipping execution")
        return "review_agent"
    return "execution_agent"


def should_run_failure_analysis(
    state: AgentState,
) -> Literal["failure_analysis_agent", "review_agent"]:
    """Route after execution: run failure analysis only if there are failures."""
    results = state.get("execution_results", {})
    if results.get("failed", 0) > 0:
        return "failure_analysis_agent"
    return "review_agent"


def handle_error(state: AgentState) -> Literal["review_agent", END]:
    """Route on error: generate a partial review or terminate."""
    errors = state.get("errors", [])
    if len(errors) > 5:
        logger.error("Too many agent errors, terminating pipeline", errors=errors)
        return END
    return "review_agent"


# ==============================================================================
# Build the LangGraph StateGraph
# ==============================================================================


def build_pr_analysis_graph() -> StateGraph:
    """Build and compile the PR analysis LangGraph pipeline.

    Returns:
        A compiled StateGraph ready for execution via .invoke() or .astream().
    """
    graph = StateGraph(AgentState)

    # --- Add agent nodes ---
    graph.add_node("planner_agent", planner_agent_node)
    graph.add_node("diff_agent", diff_agent_node)
    graph.add_node("dependency_agent", dependency_agent_node)
    graph.add_node("impact_agent", impact_agent_node)
    graph.add_node("search_agent", search_agent_node)
    graph.add_node("test_discovery_agent", test_discovery_agent_node)
    graph.add_node("test_generator_agent", test_generator_agent_node)
    graph.add_node("execution_agent", execution_agent_node)
    graph.add_node("failure_analysis_agent", failure_analysis_agent_node)
    graph.add_node("review_agent", review_agent_node)
    graph.add_node("documentation_agent", documentation_agent_node)

    # --- Define edges ---
    graph.add_edge(START, "planner_agent")
    graph.add_edge("planner_agent", "diff_agent")

    # Conditional: skip deep analysis if trivial change
    graph.add_conditional_edges(
        "diff_agent",
        should_continue_after_diff,
        {
            "dependency_agent": "dependency_agent",
            "review_agent": "review_agent",
            END: END,
        },
    )

    graph.add_edge("dependency_agent", "impact_agent")
    graph.add_edge("impact_agent", "search_agent")
    graph.add_edge("search_agent", "test_discovery_agent")
    graph.add_edge("test_discovery_agent", "test_generator_agent")

    # Conditional: skip execution if no tests generated
    graph.add_conditional_edges(
        "test_generator_agent",
        should_run_execution,
        {
            "execution_agent": "execution_agent",
            "review_agent": "review_agent",
        },
    )

    # Conditional: skip failure analysis if all tests passed
    graph.add_conditional_edges(
        "execution_agent",
        should_run_failure_analysis,
        {
            "failure_analysis_agent": "failure_analysis_agent",
            "review_agent": "review_agent",
        },
    )

    graph.add_edge("failure_analysis_agent", "review_agent")
    graph.add_edge("review_agent", "documentation_agent")
    graph.add_edge("documentation_agent", END)

    logger.info("PR analysis LangGraph pipeline compiled")
    return graph


# Compile the graph once at module load time
pr_analysis_graph = build_pr_analysis_graph().compile()
