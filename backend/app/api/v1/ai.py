import json
from pathlib import Path

import litellm
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.dependency_graph import DependencyEdge
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.schemas.ai import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CodeSearchRequest,
    CodeSearchResponse,
    CodeSearchResult,
    ImpactAnalysisRequest,
    RiskScoreRequest,
)
from app.schemas.common import APIResponse
from app.services.dependency_graph_builder import DependencyGraphBuilder
from app.utils.qdrant_client import get_qdrant_client

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
        results = qdrant.search(  # type: ignore[attr-defined]
            collection_name=settings.qdrant_collection_repository_chunks,
            query_text=last_user_message,
            limit=5,
            query_filter={
                "must": [{"key": "repository_id", "match": {"value": request.repository_id}}]
            },
        )
        for r in results:
            sources.append(r.payload.get("file_path", ""))
            context_text += (
                f"\n\n# {r.payload.get('file_path')}\n{r.payload.get('content', '')[:500]}"
            )
    except Exception as e:
        logger.warning("Qdrant search failed in chat", error=str(e))

    # Generate response with LiteLLM
    try:
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
            api_key=settings.gemini_api_key or settings.openai_api_key or None,
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
    """Semantic and structural code search using multi-layer retrieval."""
    settings = get_settings()

    # Find repository by ID or full_name
    repo_result = await db.execute(
        select(Repository).where(
            (Repository.id == request.repository_id)
            | (Repository.full_name == request.repository_id)
        )
    )
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    qdrant = get_qdrant_client()
    results: list[CodeSearchResult] = []
    seen_files: set[str] = set()
    search_term = request.query.strip().lower()

    # --------------------------------------------------------------------------
    # Layer 1: Qdrant Vector Search
    # --------------------------------------------------------------------------
    try:
        from qdrant_client.http import models as qmodels

        from app.services.embedding_service import get_embedding_service

        embedding_svc = get_embedding_service()
        query_vector = embedding_svc.generate_embedding(request.query)

        for col_name in ["code_symbols", settings.qdrant_collection_repository_chunks]:
            try:
                search_results = qdrant.search(
                    collection_name=col_name,
                    query_vector=query_vector,
                    limit=request.limit,
                    query_filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="repository_id",
                                match=qmodels.MatchValue(value=repo.id),
                            )
                        ]
                    ),
                )

                for r in search_results:
                    payload = r.payload or {}
                    file_path = payload.get("file_path", "")
                    if file_path and file_path not in seen_files:
                        seen_files.add(file_path)
                        results.append(
                            CodeSearchResult(
                                file_path=file_path,
                                language=payload.get("language") or "code",
                                snippet=payload.get("content", "")[:500],
                                score=round(float(r.score), 2),
                                function_name=payload.get("function_name"),
                                class_name=payload.get("class_name"),
                                line_start=payload.get("line_start", 1),
                                line_end=payload.get("line_end", 20),
                            )
                        )
            except Exception as search_err:
                logger.debug(
                    "Qdrant collection search attempt", col=col_name, error=str(search_err)
                )

    except Exception as e:
        logger.warning("Vector search layer failed", error=str(e))

    # --------------------------------------------------------------------------
    # Layer 2: PostgreSQL RepositoryFile Database Search
    # --------------------------------------------------------------------------
    if len(results) < request.limit:
        try:
            from app.models.repository_file import RepositoryFile

            stmt = (
                select(RepositoryFile)
                .where(
                    RepositoryFile.repository_id == repo.id,
                    (
                        RepositoryFile.path.ilike(f"%{search_term}%")
                        | RepositoryFile.functions.ilike(f"%{search_term}%")
                        | RepositoryFile.classes.ilike(f"%{search_term}%")
                        | RepositoryFile.exports.ilike(f"%{search_term}%")
                    ),
                )
                .limit(request.limit)
            )
            db_files = (await db.execute(stmt)).scalars().all()

            for db_f in db_files:
                if db_f.path not in seen_files:
                    seen_files.add(db_f.path)
                    snippet = f"File: {db_f.path}\nFunctions: {db_f.functions or '[]'}\nClasses: {db_f.classes or '[]'}"
                    results.append(
                        CodeSearchResult(
                            file_path=db_f.path,
                            language=db_f.language or "Code",
                            snippet=snippet[:500],
                            score=0.90,
                            function_name=search_term
                            if search_term in (db_f.functions or "")
                            else None,
                            class_name=search_term if search_term in (db_f.classes or "") else None,
                            line_start=1,
                            line_end=db_f.line_count or 10,
                        )
                    )
        except Exception as db_err:
            logger.warning("Postgres search layer failed", error=str(db_err))

    # --------------------------------------------------------------------------
    # Layer 3: Disk File Scanner (Searches cloned repository on disk)
    # --------------------------------------------------------------------------
    if len(results) < request.limit:
        try:
            potential_paths = [
                settings.repo_storage_path / str(repo.id),
                settings.repo_storage_path / repo.name,
                settings.repo_storage_path / repo.full_name.replace("/", "_"),
            ]

            repo_storage = next((p for p in potential_paths if p.exists() and p.is_dir()), None)

            if repo_storage and search_term:
                count = len(results)
                for path in repo_storage.rglob("*"):
                    if count >= request.limit:
                        break
                    if path.is_file() and not any(
                        part.startswith(".") or part in settings.ignored_directories
                        for part in path.parts
                    ):
                        try:
                            content = path.read_text(encoding="utf-8", errors="ignore")
                            if search_term in content.lower():
                                rel_p = str(path.relative_to(repo_storage))
                                if rel_p not in seen_files:
                                    seen_files.add(rel_p)
                                    lines = content.splitlines()
                                    matching_lines = [
                                        i
                                        for i, line_text in enumerate(lines)
                                        if search_term in line_text.lower()
                                    ]
                                    start_l = max(0, matching_lines[0] - 2) if matching_lines else 0
                                    end_l = min(len(lines), start_l + 10)
                                    snippet_text = "\n".join(lines[start_l:end_l])

                                    results.append(
                                        CodeSearchResult(
                                            file_path=rel_p,
                                            language=path.suffix.lstrip(".").upper() or "Code",
                                            snippet=snippet_text[:500],
                                            score=0.95,
                                            function_name=search_term,
                                            class_name=None,
                                            line_start=start_l + 1,
                                            line_end=end_l,
                                        )
                                    )
                                    count += 1
                        except Exception:
                            pass
        except Exception as fs_err:
            logger.warning("Disk scanner search layer failed", error=str(fs_err))

    return APIResponse(
        data=CodeSearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            search_type=request.search_type,
        )
    )


@router.post("/impact-analysis", response_model=APIResponse[dict])
async def run_impact_analysis(
    request: ImpactAnalysisRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Run manual impact analysis for a set of changed files."""
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
        select(DependencyEdge).where(DependencyEdge.repository_id == request.repository_id)
    )
    edges = edges_result.scalars().all()
    edge_records = [
        {"source_node": e.source_node, "target_node": e.target_node, "edge_type": e.edge_type}
        for e in edges
    ]

    repo_path = settings.repo_storage_path / request.repository_id
    builder = DependencyGraphBuilder.from_edge_records(edge_records, Path(repo_path))
    affected = builder.get_affected_by_changes(request.changed_files, depth=request.depth)

    all_affected = set()
    for deps in affected.values():
        all_affected.update(deps)

    return APIResponse(
        data={
            "changed_files": request.changed_files,
            "affected_modules": list(all_affected),
            "impact_radius": len(all_affected),
            "per_file": {k: list(v) for k, v in affected.items()},
        }
    )


@router.post("/risk-score", response_model=APIResponse[dict])
async def get_risk_score(
    request: RiskScoreRequest,
    db: DBSession,
    current_user: CurrentUser,
) -> APIResponse[dict]:
    """Get the risk score for a pull request."""
    result = await db.execute(select(PullRequest).where(PullRequest.id == request.pr_id))
    pr = result.scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")

    return APIResponse(
        data={
            "pr_id": pr.id,
            "risk_level": pr.risk_level,
            "risk_score": pr.risk_score,
            "risk_factors": json.loads(pr.risk_factors or "[]"),
            "analysis_status": pr.analysis_status,
        }
    )
