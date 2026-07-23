"""TestPilot AI — GitHub Webhook API."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status

from app.core.logging import get_logger
from app.core.security import verify_github_webhook_signature

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/github",
    status_code=status.HTTP_202_ACCEPTED,
    summary="GitHub Webhook Receiver",
    description="Receives GitHub App webhook events and dispatches async tasks.",
)
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
) -> dict[str, str]:
    """Receive and process GitHub webhook events.

    Verifies HMAC-SHA256 signature, then routes the event to the
    appropriate handler based on the X-GitHub-Event header.

    Supported events:
    - pull_request: opened, synchronize, closed, reopened
    - installation: created, deleted (for GitHub App)
    - ping: webhook setup verification

    Args:
        request: Raw FastAPI request.
        background_tasks: FastAPI background task runner.
        x_hub_signature_256: HMAC-SHA256 signature from GitHub.
        x_github_event: Event type identifier.
        x_github_delivery: Unique delivery UUID.

    Returns:
        Acknowledgment response with delivery ID.

    Raises:
        HTTPException: 403 if signature verification fails.
        HTTPException: 400 if payload is invalid.
    """
    payload_body = await request.body()

    # Verify webhook signature
    if not verify_github_webhook_signature(payload_body, x_hub_signature_256):
        logger.warning(
            "GitHub webhook signature verification failed",
            delivery_id=x_github_delivery,
            github_event=x_github_event,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    logger.info(
        "GitHub webhook received",
        github_event=x_github_event,
        delivery_id=x_github_delivery,
        repo=payload.get("repository", {}).get("full_name"),
    )

    # Route to appropriate handler
    if x_github_event == "ping":
        return {"status": "pong", "delivery_id": x_github_delivery or ""}

    elif x_github_event == "pull_request":
        background_tasks.add_task(_handle_pull_request_event, payload, x_github_delivery)

    elif x_github_event == "installation":
        background_tasks.add_task(_handle_installation_event, payload)

    return {
        "status": "accepted",
        "delivery_id": x_github_delivery or "",
        "event": x_github_event or "",
    }


async def _handle_pull_request_event(
    payload: dict,
    delivery_id: str | None,
) -> None:
    """Process a pull_request webhook event.

    Triggers the PR analysis pipeline for relevant actions:
    - opened: Start analysis for new PRs
    - synchronize: Re-analyze on new commits pushed
    - closed+merged: Store merged PR in historical learning
    """
    action = payload.get("action")
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})
    installation = payload.get("installation", {})

    logger.info(
        "Processing pull_request event",
        action=action,
        pr_number=pr_data.get("number"),
        repo=repo_data.get("full_name"),
    )

    if action not in ("opened", "synchronize", "reopened"):
        if action == "closed" and pr_data.get("merged"):
            await _handle_pr_merged(pr_data, repo_data)
        return

    # Look up or create the PR record and trigger analysis
    import uuid

    from sqlalchemy import select

    from app.database.session import get_session
    from app.models.pull_request import PullRequest
    from app.models.repository import Repository

    async with get_session() as db:
        repo_result = await db.execute(
            select(Repository).where(Repository.full_name == repo_data.get("full_name"))
        )
        repo = repo_result.scalar_one_or_none()

        if not repo:
            logger.warning(
                "Received webhook for unregistered repository",
                repo=repo_data.get("full_name"),
            )
            return

        # Create or update PR record
        pr_result = await db.execute(
            select(PullRequest).where(
                PullRequest.repository_id == repo.id,
                PullRequest.pr_number == pr_data.get("number"),
            )
        )
        pr = pr_result.scalar_one_or_none()

        if not pr:
            pr = PullRequest(
                id=str(uuid.uuid4()),
                repository_id=repo.id,
                pr_number=pr_data.get("number"),
                github_pr_id=str(pr_data.get("id")),
                title=pr_data.get("title", ""),
                description=pr_data.get("body"),
                state=pr_data.get("state", "open"),
                author=pr_data.get("user", {}).get("login", ""),
                base_branch=pr_data.get("base", {}).get("ref", "main"),
                head_branch=pr_data.get("head", {}).get("ref", ""),
                head_sha=pr_data.get("head", {}).get("sha", ""),
                base_sha=pr_data.get("base", {}).get("sha", ""),
                files_changed=pr_data.get("changed_files", 0),
                lines_added=pr_data.get("additions", 0),
                lines_removed=pr_data.get("deletions", 0),
                analysis_status="pending",
            )
            db.add(pr)
            await db.flush()

    # Enqueue the analysis task
    from app.tasks.pr_pipeline import run_pr_analysis

    run_pr_analysis.delay(
        pr_id=pr.id,
        repository_id=repo.id,
        repo_full_name=repo.full_name,
        pr_number=pr.pr_number,
        head_sha=pr.head_sha,
        base_sha=pr.base_sha,
        installation_id=str(installation.get("id")) if installation else None,
    )

    logger.info(
        "PR analysis task enqueued",
        pr_id=pr.id,
        pr_number=pr.pr_number,
        repo=repo.full_name,
    )


async def _handle_pr_merged(pr_data: dict, repo_data: dict) -> None:
    """Store merged PR in the historical learning knowledge base."""
    logger.info(
        "Storing merged PR in historical knowledge base",
        pr_number=pr_data.get("number"),
        repo=repo_data.get("full_name"),
    )
    # TODO: Phase 4 — extract bug signals and store in bug_history


async def _handle_installation_event(payload: dict) -> None:
    """Handle GitHub App installation events."""
    action = payload.get("action")
    installation = payload.get("installation", {})
    logger.info(
        "GitHub App installation event",
        action=action,
        installation_id=installation.get("id"),
    )
