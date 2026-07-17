"""
TestPilot AI — PR Analysis Pipeline Celery Task.

This is the main entry point for the asynchronous PR analysis workflow.
When a GitHub webhook fires for a new or updated PR, this task is enqueued
and runs the full LangGraph multi-agent pipeline.
"""

from __future__ import annotations

import asyncio
from typing import Any

from celery import Task

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


class PRPipelineTask(Task):
    """Custom Celery task with database session management.

    Inherits from Task to allow shared state across task retries.
    """

    abstract = True
    _db = None

    def on_failure(self, exc: Exception, task_id: str, args: Any, kwargs: Any, einfo: Any) -> None:
        """Handle task failure — update PR analysis status in database."""
        logger.error(
            "PR pipeline task failed",
            task_id=task_id,
            error=str(exc),
            exc_info=True,
        )
        # Update PR status to 'failed' in the database
        pr_id = kwargs.get("pr_id") or (args[0] if args else None)
        if pr_id:
            asyncio.run(_update_pr_status(pr_id, "failed", str(exc)))

    def on_success(self, retval: Any, task_id: str, args: Any, kwargs: Any) -> None:
        """Handle task success — update PR analysis status."""
        pr_id = kwargs.get("pr_id") or (args[0] if args else None)
        if pr_id:
            asyncio.run(_update_pr_status(pr_id, "completed"))


@celery_app.task(
    bind=True,
    base=PRPipelineTask,
    name="app.tasks.pr_pipeline.run_pr_analysis",
    max_retries=3,
    default_retry_delay=60,  # 1 minute before retry
    queue="pr_pipeline",
)
def run_pr_analysis(
    self: Task,
    pr_id: str,
    repository_id: str,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    base_sha: str,
    installation_id: str | None = None,
) -> dict[str, Any]:
    """Run the full PR analysis LangGraph pipeline.

    This task is triggered when a GitHub webhook fires for a PR event.
    It runs all 11 LangGraph agents in sequence and stores the results.

    Args:
        pr_id: Internal TestPilot PR UUID.
        repository_id: Internal repository UUID.
        repo_full_name: GitHub full repository name.
        pr_number: GitHub PR number.
        head_sha: HEAD commit SHA.
        base_sha: Base commit SHA.
        installation_id: Optional GitHub App installation ID.

    Returns:
        Dictionary with analysis results summary.
    """
    logger.info(
        "Starting PR analysis pipeline",
        task_id=self.request.id,
        pr_id=pr_id,
        repo=repo_full_name,
        pr_number=pr_number,
    )

    # Update PR status to 'running'
    asyncio.run(_update_pr_status(pr_id, "running"))

    try:
        from app.agents.graph import pr_analysis_graph
        from app.agents.state import AgentState

        # Build initial state
        initial_state = AgentState(
            pr_id=pr_id,
            repository_id=repository_id,
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            head_sha=head_sha,
            base_sha=base_sha,
            installation_id=installation_id,
            errors=[],
            retry_count=0,
            should_stop=False,
            current_agent="",
            completed_agents=[],
        )

        # Run the LangGraph pipeline
        final_state = pr_analysis_graph.invoke(initial_state)

        # Store results in database
        asyncio.run(_store_analysis_results(pr_id, final_state))

        logger.info(
            "PR analysis pipeline completed",
            pr_id=pr_id,
            risk_level=final_state.get("risk_score", {}).get("level", "unknown"),
            completed_agents=final_state.get("completed_agents", []),
        )

        return {
            "pr_id": pr_id,
            "status": "completed",
            "risk_level": final_state.get("risk_score", {}).get("level"),
            "risk_score": final_state.get("risk_score", {}).get("score"),
            "completed_agents": final_state.get("completed_agents", []),
            "errors": final_state.get("errors", []),
        }

    except Exception as exc:
        logger.exception("PR analysis pipeline failed", pr_id=pr_id, error=str(exc))
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except self.MaxRetriesExceededError:
            asyncio.run(_update_pr_status(pr_id, "failed", str(exc)))
            return {"pr_id": pr_id, "status": "failed", "error": str(exc)}


async def _update_pr_status(
    pr_id: str,
    status: str,
    error: str | None = None,
) -> None:
    """Update the PR analysis status in the database."""
    from sqlalchemy import update

    from app.database.session import get_session
    from app.models.pull_request import PullRequest

    async with get_session() as db:
        stmt = (
            update(PullRequest)
            .where(PullRequest.id == pr_id)
            .values(analysis_status=status, analysis_error=error)
        )
        await db.execute(stmt)


async def _store_analysis_results(pr_id: str, state: dict[str, Any]) -> None:
    """Store the complete analysis results in the database."""
    import json

    from sqlalchemy import update

    from app.database.session import get_session
    from app.models.pull_request import PullRequest
    from app.models.review_comment import ReviewComment

    async with get_session() as db:
        risk_score = state.get("risk_score", {})
        review = state.get("review", {})

        # Update PR with analysis results
        await db.execute(
            update(PullRequest)
            .where(PullRequest.id == pr_id)
            .values(
                analysis_status="completed",
                risk_level=risk_score.get("level"),
                risk_score=risk_score.get("score"),
                risk_factors=json.dumps(risk_score.get("factors", [])),
                affected_modules=json.dumps(state.get("affected_modules", [])),
            )
        )

        # Store the review comment
        if review:
            db.add(
                ReviewComment(
                    pull_request_id=pr_id,
                    body=review.get("full_review_body", ""),
                    risk_level=review.get("risk_level", "low"),
                    risk_score=review.get("risk_score", 0.0),
                    summary=review.get("summary"),
                    action_items=json.dumps(review.get("action_items", [])),
                    is_posted=False,
                )
            )

        logger.info("Analysis results stored", pr_id=pr_id)
