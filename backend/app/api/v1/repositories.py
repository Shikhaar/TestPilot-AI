"""TestPilot AI — Repository API."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.api.deps import CurrentUser, DBSession
from app.core.logging import get_logger
from app.schemas.common import APIResponse, PaginatedResponse, TaskResponse
from app.schemas.repository import (
    RepositoryConnectRequest,
    RepositoryIndexRequest,
    RepositoryResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("", response_model=PaginatedResponse[RepositoryResponse])
async def list_repositories(
    db: DBSession,
    current_user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[RepositoryResponse]:
    """List all repositories connected by the current user."""
    from sqlalchemy import func, select

    from app.models.repository import Repository

    offset = (page - 1) * page_size

    total_result = await db.execute(
        select(func.count()).select_from(Repository).where(Repository.owner_id == current_user.id)
    )
    total = total_result.scalar_one()

    repos_result = await db.execute(
        select(Repository)
        .where(Repository.owner_id == current_user.id)
        .order_by(Repository.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    repos = repos_result.scalars().all()

    items = [RepositoryResponse.model_validate(r) for r in repos]
    return PaginatedResponse.create(items, total, page, page_size)


@router.post(
    "/connect",
    response_model=APIResponse[RepositoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def connect_repository(
    request: RepositoryConnectRequest,
    db: DBSession,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> APIResponse[RepositoryResponse]:
    """Connect a GitHub repository to TestPilot AI.

    Fetches repository metadata from GitHub, creates a database record,
    and enqueues an initial indexing job.
    """
    import uuid

    from sqlalchemy import select

    from app.models.repository import Repository
    from app.services.github_service import GitHubService

    # Check if already connected
    existing = await db.execute(select(Repository).where(Repository.full_name == request.full_name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository '{request.full_name}' is already connected",
        )

    # Fetch repository metadata from GitHub
    github = GitHubService()
    try:
        gh_repo = github.get_repository(
            request.full_name,
            access_token=current_user.github_access_token,
            installation_id=request.github_app_installation_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not access GitHub repository: {e}",
        ) from e

    # Create repository record
    repo = Repository(
        id=str(uuid.uuid4()),
        owner_id=current_user.id,
        github_repo_id=str(gh_repo.id),
        full_name=gh_repo.full_name,
        name=gh_repo.name,
        owner_login=gh_repo.owner.login,
        description=gh_repo.description,
        clone_url=gh_repo.clone_url,
        ssh_url=gh_repo.ssh_url,
        default_branch=gh_repo.default_branch,
        language=gh_repo.language,
        is_private=gh_repo.private,
        github_app_installation_id=request.github_app_installation_id,
        index_status="pending",
    )
    db.add(repo)
    await db.flush()

    # Trigger background indexing
    background_tasks.add_task(
        _trigger_indexing, repo.id, repo.clone_url, current_user.github_access_token
    )

    logger.info("Repository connected", repo_id=repo.id, full_name=repo.full_name)

    return APIResponse(
        data=RepositoryResponse.model_validate(repo),
        message="Repository connected. Indexing has been queued.",
    )


@router.get("/{repo_id}", response_model=APIResponse[RepositoryResponse])
async def get_repository(
    repo_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[RepositoryResponse]:
    """Get a specific repository by ID."""
    from sqlalchemy import select

    from app.models.repository import Repository

    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    return APIResponse(data=RepositoryResponse.model_validate(repo))


@router.post("/{repo_id}/index", response_model=TaskResponse)
async def trigger_reindex(
    repo_id: str,
    request: RepositoryIndexRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> TaskResponse:
    """Trigger re-indexing of a repository."""
    from sqlalchemy import select

    from app.models.repository import Repository

    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    if repo.index_status == "indexing" and not request.force_reindex:
        return TaskResponse(
            task_id="",
            status="already_running",
            message="Repository is already being indexed",
        )

    from app.tasks.indexing import index_repository

    task = index_repository.delay(
        repository_id=repo.id,
        clone_url=repo.clone_url,
        access_token=current_user.github_access_token,
        force_reindex=request.force_reindex,
    )

    logger.info("Repository re-index triggered", repo_id=repo_id, task_id=task.id)

    return TaskResponse(
        task_id=task.id,
        status="queued",
        message="Repository indexing has been queued",
        estimated_duration_seconds=120,
    )


async def _trigger_indexing(
    repo_id: str,
    clone_url: str,
    access_token: str | None,
) -> None:
    """Enqueue repository indexing as a background task."""
    from app.tasks.indexing import index_repository

    index_repository.delay(
        repository_id=repo_id,
        clone_url=clone_url,
        access_token=access_token,
    )
