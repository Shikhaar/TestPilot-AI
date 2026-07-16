"""TestPilot AI — AI/Chat/Search API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DBSession
from app.core.logging import get_logger
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    CodeSearchRequest,
    CodeSearchResponse,
    ImpactAnalysisRequest,
    RiskScoreRequest,
)
from app.schemas.common import APIResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_codebase(
    request: ChatRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> ChatResponse:
    """Chat with the codebase using natural language.

    Uses RAG (Retrieval-Augmented Generation) to ground responses
    in the actual repository code.
    """
    from sqlalchemy import select
    from app.models.repository import Repository
    from app.utils.qdrant_client import get_qdrant_client
    from app.core.config import get_settings
    settings = get_settings()

    # Verify repository access
    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == request.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Retrieve relevant code context
    qdrant = get_qdrant_client()
    last_user_message = next(
        (m.content for m in reversed(request.messages) if m.role == "user"), ""
    )

    sources = []
    context_text = ""

    try:
        results = qdrant.search(
            collection_name=settings.qdrant_collection_repository_chunks,
            query_text=last_user_message,
            limit=5,
            query_filter={
                "must": [{"key": "repository_id", "match": {"value": request.repository_id}}]
            },
        )
        for r in results:
            sources.append(r.payload.get("file_path", ""))
            context_text += f"\n\n# {r.payload.get('file_path')}\n{r.payload.get('content', '')[:500]}"
    except Exception as e:
        logger.warning("Qdrant search failed in chat", error=str(e))

    # Generate response with LiteLLM
    try:
        import litellm
        messages = [
            {
                "role": "system",
                "content": f"You are a code assistant for the {repo.full_name} repository. "
                          f"Answer questions based on the following code context:\n{context_text}",
            }
        ] + [{"role": m.role, "content": m.content} for m in request.messages]

        response = litellm.completion(
            model=settings.litellm_default_model,
            messages=messages,
            max_tokens=request.max_tokens,
        )
        answer = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0

    except Exception as e:
        logger.warning("LiteLLM chat failed", error=str(e))
        answer = "AI assistant is temporarily unavailable. Please try again later."
        tokens = 0

    return ChatResponse(
        message=ChatMessage(role="assistant", content=answer),
        sources=list(set(sources)),
        tokens_used=tokens,
    )


@router.post("/search", response_model=APIResponse[CodeSearchResponse])
async def search_code(
    request: CodeSearchRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[CodeSearchResponse]:
    """Semantic and structural code search."""
    from sqlalchemy import select
    from app.models.repository import Repository
    from app.utils.qdrant_client import get_qdrant_client
    from app.core.config import get_settings
    from app.schemas.ai import CodeSearchResult
    settings = get_settings()

    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == request.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    qdrant = get_qdrant_client()
    results = []

    try:
        search_results = qdrant.search(
            collection_name=settings.qdrant_collection_repository_chunks,
            query_text=request.query,
            limit=request.limit,
            query_filter={
                "must": [{"key": "repository_id", "match": {"value": request.repository_id}}]
            },
        )

        for r in search_results:
            results.append(
                CodeSearchResult(
                    file_path=r.payload.get("file_path", ""),
                    language=r.payload.get("language", ""),
                    snippet=r.payload.get("content", "")[:300],
                    score=r.score,
                    function_name=r.payload.get("function_name"),
                    class_name=r.payload.get("class_name"),
                    line_start=r.payload.get("line_start"),
                    line_end=r.payload.get("line_end"),
                )
            )
    except Exception as e:
        logger.warning("Code search failed", error=str(e))

    return APIResponse(data=CodeSearchResponse(
        results=results,
        total=len(results),
        query=request.query,
        search_type=request.search_type,
    ))


@router.post("/impact-analysis", response_model=APIResponse[dict])
async def run_impact_analysis(
    request: ImpactAnalysisRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Run manual impact analysis for a set of changed files."""
    from sqlalchemy import select
    from app.models.repository import Repository
    from app.models.dependency_graph import DependencyEdge
    from app.services.dependency_graph_builder import DependencyGraphBuilder
    from app.core.config import get_settings
    from pathlib import Path
    settings = get_settings()

    repo_result = await db.execute(
        select(Repository).where(
            Repository.id == request.repository_id,
            Repository.owner_id == current_user.id,
        )
    )
    if not repo_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Repository not found")

    edges_result = await db.execute(
        select(DependencyEdge).where(
            DependencyEdge.repository_id == request.repository_id
        )
    )
    edges = edges_result.scalars().all()
    edge_records = [{"source_node": e.source_node, "target_node": e.target_node, "edge_type": e.edge_type} for e in edges]

    repo_path = settings.repo_storage_path / request.repository_id
    builder = DependencyGraphBuilder.from_edge_records(edge_records, Path(repo_path))
    affected = builder.get_affected_by_changes(request.changed_files, depth=request.depth)

    all_affected = set()
    for deps in affected.values():
        all_affected.update(deps)

    return APIResponse(data={
        "changed_files": request.changed_files,
        "affected_modules": list(all_affected),
        "impact_radius": len(all_affected),
        "per_file": {k: list(v) for k, v in affected.items()},
    })


@router.post("/risk-score", response_model=APIResponse[dict])
async def get_risk_score(
    request: RiskScoreRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Get the risk score for a pull request."""
    from sqlalchemy import select
    from app.models.pull_request import PullRequest
    import json

    result = await db.execute(select(PullRequest).where(PullRequest.id == request.pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")

    return APIResponse(data={
        "pr_id": pr.id,
        "risk_level": pr.risk_level,
        "risk_score": pr.risk_score,
        "risk_factors": json.loads(pr.risk_factors or "[]"),
        "analysis_status": pr.analysis_status,
    })
