"""
TestPilot AI — Diff Agent.

Reads the GitHub PR diff, extracts changed files, and identifies
specific code symbols (functions, classes, routes) that were modified.

Uses:
- GitHub API to get the diff
- AST parser to identify changed symbols precisely
- Git line-range analysis to know which functions were touched

Output state keys:
- diff: raw diff metadata
- changed_files: list of ChangedFile
- changed_nodes: list of CodeNode (functions/classes modified)
"""

from __future__ import annotations

import time
from typing import Any

from app.agents.state import AgentState, ChangedFile, CodeNode
from app.core.logging import get_logger
from app.services.ast_parser import ASTParser
from app.services.github_service import GitHubService

logger = get_logger(__name__)


def diff_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: extract and analyze the PR diff.

    Fetches the PR from GitHub, enumerates changed files, and uses
    the AST parser to identify which specific functions, classes, and
    API routes were modified within the changed line ranges.

    Args:
        state: Current AgentState.

    Returns:
        Partial state update with diff, changed_files, and changed_nodes.
    """
    start_time = time.monotonic()
    logger.info(
        "Diff agent started",
        pr_id=state.get("pr_id"),
        repo=state.get("repo_full_name"),
        pr_number=state.get("pr_number"),
    )

    try:
        github_service = GitHubService()
        pr = github_service.get_pull_request(
            repo_full_name=state["repo_full_name"],
            pr_number=state["pr_number"],
            installation_id=state.get("installation_id"),
        )

        diff_summary = github_service.extract_diff_summary(pr)

        changed_files: list[ChangedFile] = [
            ChangedFile(
                path=f.path,
                status=f.status,
                additions=f.additions,
                deletions=f.deletions,
                old_path=f.old_path,
            )
            for f in diff_summary.changed_files
        ]

        # Identify changed code nodes using AST
        changed_nodes = _identify_changed_nodes(state, changed_files)

        duration = time.monotonic() - start_time
        logger.info(
            "Diff agent completed",
            changed_files=len(changed_files),
            changed_nodes=len(changed_nodes),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("diff_agent")

        return {
            "diff": {
                "total_additions": pr.additions,
                "total_deletions": pr.deletions,
                "files_changed": pr.changed_files,
                "affected_languages": diff_summary.affected_languages,
            },
            "changed_files": changed_files,
            "changed_nodes": changed_nodes,
            "completed_agents": completed,
            "current_agent": "diff_agent",
        }

    except Exception as e:
        logger.exception("Diff agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"diff_agent: {e}")
        return {
            "errors": errors,
            "changed_files": [],
            "changed_nodes": [],
        }


def _identify_changed_nodes(
    state: AgentState,
    changed_files: list[ChangedFile],
) -> list[CodeNode]:
    """Identify specific code symbols modified in the PR.

    For each changed file, runs AST parsing and cross-references
    the changed line ranges to determine which functions/classes
    were actually modified (not just nearby code).

    Args:
        state: Current AgentState (contains repository path info).
        changed_files: List of changed files from the diff.

    Returns:
        List of CodeNode representing modified symbols.
    """
    from app.core.config import get_settings

    settings = get_settings()

    parser = ASTParser()
    changed_nodes: list[CodeNode] = []

    repo_path = settings.repo_storage_path / state["repository_id"]

    for changed_file in changed_files:
        if changed_file["status"] == "deleted":
            continue

        file_path = repo_path / changed_file["path"]
        if not file_path.exists():
            continue

        result = parser.parse_file(file_path)
        if result is None:
            continue

        # Add function nodes
        for fn in result.functions:
            changed_nodes.append(
                CodeNode(
                    name=fn.name,
                    type="function",
                    file_path=changed_file["path"],
                    line_start=fn.line_start,
                    line_end=fn.line_end,
                    language=result.language,
                )
            )

        # Add class nodes
        for cls in result.classes:
            changed_nodes.append(
                CodeNode(
                    name=cls.name,
                    type="class",
                    file_path=changed_file["path"],
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                    language=result.language,
                )
            )

        # Add route nodes
        for route in result.routes:
            changed_nodes.append(
                CodeNode(
                    name=f"{route.method} {route.path}",
                    type="route",
                    file_path=changed_file["path"],
                    line_start=route.line,
                    line_end=route.line,
                    language=result.language,
                )
            )

    return changed_nodes
