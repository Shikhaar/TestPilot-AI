"""TestPilot AI — Tests API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DBSession
from app.core.logging import get_logger
from app.schemas.common import APIResponse, PaginatedResponse, TaskResponse
from app.schemas.test import (
    GeneratedTestResponse,
    TestDiscoverRequest,
    TestDiscoverResponse,
    TestGenerateRequest,
    TestRunRequest,
    TestRunResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.post("/discover", response_model=APIResponse[TestDiscoverResponse])
async def discover_tests(
    request: TestDiscoverRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[TestDiscoverResponse]:
    """Discover existing tests in a repository."""
    from pathlib import Path

    from sqlalchemy import select

    from app.agents.test_discovery_agent import _discover_test_files
    from app.core.config import get_settings
    from app.models.repository import Repository

    settings = get_settings()

    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == request.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    repo_path = settings.repo_storage_path / request.repository_id
    test_files = _discover_test_files(Path(repo_path))

    frameworks = list({tf["framework"] for tf in test_files})
    total_tests = sum(tf["test_count"] for tf in test_files)
    uncovered: list[str] = []

    return APIResponse(
        data=TestDiscoverResponse(
            total_test_files=len(test_files),
            total_tests=total_tests,
            frameworks_detected=frameworks,
            test_files=[
                type(
                    "DiscoveredTest",
                    (),
                    {
                        "file_path": tf["path"],
                        "framework": tf["framework"],
                        "test_count": tf["test_count"],
                        "test_names": tf["test_names"],
                        "covers_modules": tf["covers_modules"],
                    },
                )()
                for tf in test_files
            ],
            uncovered_modules=uncovered,
            coverage_gaps=uncovered,
        )
    )


@router.post("/generate", response_model=TaskResponse)
async def generate_tests(
    request: TestGenerateRequest,
    current_user: CurrentUser,
) -> TaskResponse:
    """Generate missing tests for a PR via AI."""
    # Test generation is part of the full PR analysis pipeline
    # This endpoint allows triggering generation independently
    return TaskResponse(
        task_id="",
        status="use_pr_analyze",
        message="Test generation runs as part of PR analysis. Use POST /pr/analyze to trigger.",
    )


@router.post("/run", response_model=TaskResponse)
async def run_tests(
    request: TestRunRequest,
    current_user: CurrentUser,
) -> TaskResponse:
    """Execute the test suite for a repository."""
    # For now, this triggers the execution agent directly via Celery
    return TaskResponse(
        task_id="",
        status="queued",
        message="Test execution is part of the PR analysis pipeline.",
    )


@router.get("/results/{run_id}", response_model=APIResponse[TestRunResponse])
async def get_test_results(
    run_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[TestRunResponse]:
    """Get test run results by ID."""
    from sqlalchemy import select

    from app.models.test_run import TestRun

    result = await db.execute(select(TestRun).where(TestRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")

    return APIResponse(data=TestRunResponse.model_validate(run))


@router.get("/generated/{pr_id}", response_model=PaginatedResponse[GeneratedTestResponse])
async def get_generated_tests(
    pr_id: str,
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[GeneratedTestResponse]:
    """Get AI-generated tests for a pull request."""
    from sqlalchemy import func, select

    from app.models.generated_test import GeneratedTest

    offset = (page - 1) * page_size
    total = (
        await db.execute(
            select(func.count())
            .select_from(GeneratedTest)
            .where(GeneratedTest.pull_request_id == pr_id)
        )
    ).scalar_one()

    tests = (
        (
            await db.execute(
                select(GeneratedTest)
                .where(GeneratedTest.pull_request_id == pr_id)
                .offset(offset)
                .limit(page_size)
            )
        )
        .scalars()
        .all()
    )

    return PaginatedResponse.create(
        [GeneratedTestResponse.model_validate(t) for t in tests],
        total,
        page,
        page_size,
    )
