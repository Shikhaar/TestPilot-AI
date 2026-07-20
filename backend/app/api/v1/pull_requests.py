"""TestPilot AI — Pull Requests API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DBSession
from app.core.logging import get_logger
from app.schemas.common import APIResponse, PaginatedResponse, TaskResponse
from app.schemas.pull_request import (
    PRAnalyzeRequest,
    PullRequestDetailResponse,
    PullRequestResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[PullRequestResponse])
async def list_pull_requests(
    db: DBSession,
    current_user: CurrentUser,
    repository_id: str | None = None,
    state: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[PullRequestResponse]:
    """List pull requests with optional filtering."""
    from sqlalchemy import func, select

    from app.models.pull_request import PullRequest
    from app.models.repository import Repository

    offset = (page - 1) * page_size

    stmt = (
        select(PullRequest)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .where(Repository.owner_id == current_user.id)
    )

    if repository_id:
        stmt = stmt.where(PullRequest.repository_id == repository_id)
    if state:
        stmt = stmt.where(PullRequest.state == state)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    prs = (
        (
            await db.execute(
                stmt.order_by(PullRequest.created_at.desc()).offset(offset).limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    return PaginatedResponse.create(
        [PullRequestResponse.model_validate(pr) for pr in prs],
        total,
        page,
        page_size,
    )


@router.get("/{pr_id}", response_model=APIResponse[PullRequestDetailResponse])
async def get_pull_request(
    pr_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[PullRequestDetailResponse]:
    """Get detailed pull request analysis results."""
    import json

    from sqlalchemy import select

    from app.models.pull_request import PullRequest
    from app.models.repository import Repository

    result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(PullRequest.id == pr_id, Repository.owner_id == current_user.id)
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")

    response = PullRequestDetailResponse(
        **PullRequestResponse.model_validate(pr).model_dump(),
        affected_modules=json.loads(pr.affected_modules or "[]"),
        risk_factors=json.loads(pr.risk_factors or "[]"),
    )
    return APIResponse(data=response)


@router.post("/analyze", response_model=TaskResponse)
async def trigger_pr_analysis(
    request: PRAnalyzeRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> TaskResponse:
    """Manually trigger analysis for a specific pull request."""
    from sqlalchemy import select

    from app.models.pull_request import PullRequest
    from app.models.repository import Repository

    result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(
            PullRequest.id == request.pr_id
            if hasattr(request, "pr_id")
            else PullRequest.pr_number == request.pr_number,
            Repository.id == request.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")

    from app.tasks.pr_pipeline import run_pr_analysis

    task = run_pr_analysis.delay(
        pr_id=pr.id,
        repository_id=pr.repository_id,
        repo_full_name=pr.repository.full_name if pr.repository else "",
        pr_number=pr.pr_number,
        head_sha=pr.head_sha,
        base_sha=pr.base_sha,
    )

    return TaskResponse(
        task_id=task.id,
        status="queued",
        message="PR analysis queued",
        estimated_duration_seconds=60,
    )


@router.post("/{pr_id}/review", response_model=APIResponse[dict])
async def post_github_review(
    pr_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Post the AI-generated review to GitHub."""
    from sqlalchemy import select

    from app.models.pull_request import PullRequest
    from app.models.repository import Repository
    from app.models.review_comment import ReviewComment
    from app.services.github_service import GitHubService

    pr_result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(
            PullRequest.id == pr_id,
            Repository.owner_id == current_user.id,
        )
    )
    pr = pr_result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")

    review_result = await db.execute(
        select(ReviewComment).where(
            ReviewComment.pull_request_id == pr_id,
            ReviewComment.is_posted.is_(False),
        )
    )
    review = review_result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="No pending review to post")

    github = GitHubService()
    repo = pr.repository
    result = github.post_pr_review(
        repo_full_name=repo.full_name,
        pr_number=pr.pr_number,
        body=review.body,
        access_token=current_user.github_access_token,
    )

    review.is_posted = True
    review.github_review_id = result["review_id"]

    return APIResponse(data=result, message="Review posted to GitHub successfully")
