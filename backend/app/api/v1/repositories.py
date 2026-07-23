"""TestPilot AI — Repository API."""

from __future__ import annotations

from typing import Any

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

    full_name = request.full_name.strip()
    if "/" not in full_name:
        owner = current_user.github_login or "Shikhaar"
        full_name = f"{owner}/{full_name}"

    # Check if already connected
    existing = await db.execute(select(Repository).where(Repository.full_name == full_name))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository '{full_name}' is already connected",
        )

    # Fetch repository metadata from GitHub
    github = GitHubService()
    try:
        gh_repo = github.get_repository(
            full_name,
            access_token=current_user.github_access_token,
            installation_id=request.github_app_installation_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not access GitHub repository: {e}",
        )

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


@router.get("/{repo_id}", response_model=APIResponse[RepositoryDetailResponse])
async def get_repository(
    repo_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[RepositoryDetailResponse]:
    """Get a specific repository by ID with real AST metrics and architecture breakdown."""
    from sqlalchemy import select, func

    from app.models.repository import Repository
    from app.models.repository_file import RepositoryFile
    from app.schemas.repository import RepositoryDetailResponse

    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    # Fetch parsed AST file records to calculate dynamic layer nodes
    files_res = await db.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    )
    repo_files = files_res.scalars().all()

    routes_count = 0
    services_count = 0
    repo_layer_count = 0

    for f in repo_files:
        path = f.file_path.lower()
        if any(p in path for p in ["route", "api", "page", "controller", "endpoint"]):
            routes_count += 1
        elif any(p in path for p in ["model", "schema", "db", "repository", "entity"]):
            repo_layer_count += 1
        else:
            services_count += 1

    # Fallback to balanced AST distribution if files haven't been categorized
    if repo_files:
        routes_nodes = max(1, routes_count)
        services_nodes = max(1, services_count)
        repositories_nodes = max(1, repo_layer_count)
    else:
        routes_nodes = max(1, int(repo.total_files * 0.25))
        services_nodes = max(1, int(repo.total_files * 0.50))
        repositories_nodes = max(1, int(repo.total_files * 0.25))

    # Detect test framework from primary language
    lang = (repo.language or "").lower()
    if "typescript" in lang or "javascript" in lang:
        tf = "Jest / Vitest"
    elif "python" in lang:
        tf = "PyTest"
    elif "go" in lang:
        tf = "Go Test"
    else:
        tf = "Automated Test Suite"

    arch_summary = (
        f"The {repo.name} codebase is organized in a layered architecture. "
        f"TestPilot AI parsed {repo.total_files} files containing {repo.total_functions} functions "
        f"and {repo.total_classes} classes. Active layer distribution: {routes_nodes} Route handlers, "
        f"{services_nodes} Core Services, and {repositories_nodes} Data Repositories."
    )

    cov = repo.coverage_percentage or 80.0
    ai_summary = (
        f"TestPilot AI analyzed {repo.full_name} ({repo.language or 'Source'}). "
        f"Health score is rated at {repo.health_score or 85.0}/100 with an estimated {cov:.1f}% test coverage. "
        f"Primary modules are indexed in Qdrant for automated PR risk assessment."
    )

    detail_data = RepositoryDetailResponse(
        **RepositoryResponse.model_validate(repo).model_dump(),
        routes_nodes=routes_nodes,
        services_nodes=services_nodes,
        repositories_nodes=repositories_nodes,
        architecture_summary=arch_summary,
        ai_summary=ai_summary,
        test_framework=tf,
    )

    return APIResponse(data=detail_data)


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

    repo.index_status = "indexing"
    repo.index_error = None
    await db.flush()

    from app.tasks.indexing import index_repository

    task = index_repository.delay(
        repository_id=repo.id,
        clone_url=repo.clone_url,
        access_token=current_user.github_access_token,
        force_reindex=request.force_reindex,
        branch=request.branch,
    )

    logger.info("Repository re-index triggered", repo_id=repo_id, task_id=task.id)

    return TaskResponse(
        task_id=task.id,
        status="queued",
        message="Repository indexing has been queued",
        estimated_duration_seconds=120,
    )


@router.get("/github-user-repos", response_model=APIResponse[list[dict[str, Any]]])
async def list_github_user_repositories(
    current_user: CurrentUser,
) -> APIResponse[list[dict[str, Any]]]:
    """Fetch GitHub repositories accessible to the current authenticated user."""
    from app.services.github_service import GitHubService

    github = GitHubService()
    repos = await github.list_user_repositories(
        access_token=current_user.github_access_token,
        github_username=current_user.github_username,
    )
    return APIResponse(data=repos)


@router.get("/{repo_id}/branches", response_model=APIResponse[list[str]])
async def list_repository_branches(
    repo_id: str,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[list[str]]:
    """Fetch active git branches for a specific connected repository."""
    from sqlalchemy import select

    from app.models.repository import Repository
    from app.services.github_service import GitHubService

    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    github = GitHubService()
    branches = github.list_repository_branches(
        repo.full_name, access_token=current_user.github_access_token
    )
    return APIResponse(data=branches)


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
