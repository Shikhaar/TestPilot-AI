"""TestPilot AI — Dashboard API."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession
from app.core.logging import get_logger
from app.schemas.common import APIResponse

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=APIResponse[dict])
async def get_dashboard(
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Get aggregated dashboard metrics for the current user."""
    from sqlalchemy import func, select
    from app.models.repository import Repository
    from app.models.pull_request import PullRequest
    from app.models.generated_test import GeneratedTest
    from app.models.test_run import TestRun

    # Repository stats
    repo_count = (await db.execute(
        select(func.count()).select_from(Repository).where(Repository.owner_id == current_user.id)
    )).scalar_one()

    indexed_count = (await db.execute(
        select(func.count()).select_from(Repository).where(
            Repository.owner_id == current_user.id,
            Repository.is_indexed.is_(True),
        )
    )).scalar_one()

    # PR stats
    total_prs = (await db.execute(
        select(func.count()).select_from(PullRequest)
        .join(Repository)
        .where(Repository.owner_id == current_user.id)
    )).scalar_one()

    critical_prs = (await db.execute(
        select(func.count()).select_from(PullRequest)
        .join(Repository)
        .where(
            Repository.owner_id == current_user.id,
            PullRequest.risk_level == "critical",
        )
    )).scalar_one()

    active_prs = (await db.execute(
        select(func.count()).select_from(PullRequest)
        .join(Repository)
        .where(
            Repository.owner_id == current_user.id,
            PullRequest.analysis_status.in_(["pending", "running"]),
        )
    )).scalar_one()

    completed_prs = (await db.execute(
        select(func.count()).select_from(PullRequest)
        .join(Repository)
        .where(
            Repository.owner_id == current_user.id,
            PullRequest.analysis_status == "completed",
        )
    )).scalar_one()

    failed_prs = (await db.execute(
        select(func.count()).select_from(PullRequest)
        .join(Repository)
        .where(
            Repository.owner_id == current_user.id,
            PullRequest.analysis_status == "failed",
        )
    )).scalar_one()

    total_finished = completed_prs + failed_prs
    success_rate = (completed_prs / total_finished * 100.0) if total_finished > 0 else 100.0

    # Generated tests
    total_generated = (await db.execute(
        select(func.count()).select_from(GeneratedTest)
        .join(Repository, GeneratedTest.repository_id == Repository.id)
        .where(Repository.owner_id == current_user.id)
    )).scalar_one()

    # Recent PRs
    recent_prs_result = await db.execute(
        select(PullRequest)
        .join(Repository)
        .where(Repository.owner_id == current_user.id)
        .order_by(PullRequest.created_at.desc())
        .limit(5)
    )
    recent_prs = recent_prs_result.scalars().all()

    return APIResponse(data={
        "repositories": {
            "total": repo_count,
            "indexed": indexed_count,
            "pending": repo_count - indexed_count,
        },
        "pull_requests": {
            "total": total_prs,
            "critical": critical_prs,
            "active": active_prs,
            "success_rate": round(success_rate, 1),
        },
        "tests": {
            "generated": total_generated,
        },
        "recent_pull_requests": [
            {
                "id": pr.id,
                "pr_number": pr.pr_number,
                "title": pr.title,
                "state": pr.state,
                "risk_level": pr.risk_level,
                "risk_score": pr.risk_score,
                "analysis_status": pr.analysis_status,
                "created_at": pr.created_at.isoformat(),
            }
            for pr in recent_prs
        ],
    })


@router.get("/metrics", response_model=APIResponse[dict])
async def get_metrics(
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Get detailed metrics for the current user's repositories."""
    from sqlalchemy import func, select
    from app.models.repository import Repository
    from app.models.ai_log import AILog

    # AI usage stats
    token_usage = (await db.execute(
        select(func.sum(AILog.total_tokens)).select_from(AILog)
    )).scalar_one()

    cost_estimate = (await db.execute(
        select(func.sum(AILog.cost_usd)).select_from(AILog)
    )).scalar_one()

    avg_coverage = (await db.execute(
        select(func.avg(Repository.coverage_percentage)).where(
            Repository.owner_id == current_user.id,
            Repository.coverage_percentage.isnot(None),
        )
    )).scalar_one()

    return APIResponse(data={
        "ai_usage": {
            "total_tokens": token_usage or 0,
            "estimated_cost_usd": round(cost_estimate or 0, 4),
        },
        "coverage": {
            "average_percentage": round(avg_coverage or 0, 1),
        },
    })
