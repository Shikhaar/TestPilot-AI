"""
TestPilot AI — Repository Indexing Celery Task.

Handles the full repository indexing workflow:
1. Clone or update the repository via GitPython
2. Walk all files using ASTParser
3. Build dependency graph
4. Generate embeddings and store in Qdrant
5. Persist all data to PostgreSQL
"""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from pathlib import Path
from typing import Any

from celery import Task

from app.workers.celery_app import celery_app
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@celery_app.task(
    bind=True,
    name="app.tasks.indexing.index_repository",
    max_retries=2,
    default_retry_delay=120,
    queue="indexing",
    soft_time_limit=1800,
    time_limit=2700,
)
def index_repository(
    self: Task,
    repository_id: str,
    clone_url: str,
    access_token: str | None = None,
    force_reindex: bool = False,
) -> dict[str, Any]:
    """Full repository indexing pipeline.

    Clones (or pulls) the repository, parses all source files with
    Tree-sitter, builds the dependency graph, generates embeddings,
    and stores everything in PostgreSQL and Qdrant.

    Args:
        repository_id: Internal repository UUID.
        clone_url: HTTPS clone URL.
        access_token: Optional GitHub OAuth token for private repos.
        force_reindex: If True, re-index even if already indexed.

    Returns:
        Dictionary with indexing results summary.
    """
    logger.info("Starting repository indexing", repository_id=repository_id, clone_url=clone_url)

    asyncio.run(_update_repo_status(repository_id, "indexing"))

    try:
        start_time = time.monotonic()
        repo_path = settings.repo_storage_path / repository_id

        # Step 1: Clone or update repository
        _clone_or_pull(clone_url, repo_path, access_token)

        # Step 2: Parse all files with AST
        from app.services.ast_parser import ASTParser
        parser = ASTParser()
        parse_results = parser.parse_directory(repo_path)

        # Step 3: Build dependency graph
        from app.services.dependency_graph_builder import DependencyGraphBuilder
        builder = DependencyGraphBuilder(repo_path)
        builder.build(parse_results)
        edge_records = builder.to_edge_records(repository_id)

        # Step 4: Store everything in PostgreSQL
        stats = asyncio.run(
            _persist_index_results(repository_id, parse_results, edge_records, repo_path)
        )

        # Step 5: Generate and store embeddings in Qdrant
        asyncio.run(_generate_and_store_embeddings(repository_id, parse_results, repo_path))

        duration = time.monotonic() - start_time
        logger.info(
            "Repository indexing completed",
            repository_id=repository_id,
            files=stats["files"],
            functions=stats["functions"],
            classes=stats["classes"],
            edges=len(edge_records),
            duration_s=round(duration, 1),
        )

        asyncio.run(_update_repo_status(repository_id, "indexed", stats=stats))

        return {
            "repository_id": repository_id,
            "status": "indexed",
            **stats,
            "duration_seconds": round(duration, 1),
        }

    except Exception as exc:
        logger.exception("Repository indexing failed", repository_id=repository_id, error=str(exc))
        asyncio.run(_update_repo_status(repository_id, "failed", error=str(exc)))

        try:
            raise self.retry(exc=exc, countdown=120)
        except self.MaxRetriesExceededError:
            return {"repository_id": repository_id, "status": "failed", "error": str(exc)}


def _clone_or_pull(clone_url: str, repo_path: Path, access_token: str | None) -> None:
    """Clone a repository or pull latest if already cloned."""
    import git

    # Inject access token into URL for private repos
    if access_token and "github.com" in clone_url:
        clone_url = clone_url.replace("https://", f"https://x-access-token:{access_token}@")

    if repo_path.exists() and (repo_path / ".git").exists():
        logger.info("Pulling repository updates", path=str(repo_path))
        repo = git.Repo(repo_path)
        repo.remotes.origin.pull()
    else:
        logger.info("Cloning repository", url=clone_url, path=str(repo_path))
        repo_path.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(
            clone_url,
            repo_path,
            depth=50,  # Shallow clone for performance
        )


async def _persist_index_results(
    repository_id: str,
    parse_results: list[Any],
    edge_records: list[dict[str, Any]],
    repo_path: Path,
) -> dict[str, int]:
    """Persist parsed AST results and dependency graph to PostgreSQL."""
    from app.database.session import get_session
    from app.models.repository_file import RepositoryFile
    from app.models.dependency_graph import DependencyEdge
    from sqlalchemy import delete

    total_functions = 0
    total_classes = 0
    file_records = []

    for result in parse_results:
        if result.error:
            continue
        try:
            rel_path = str(Path(result.file_path).relative_to(repo_path))
        except ValueError:
            rel_path = result.file_path

        total_functions += len(result.functions)
        total_classes += len(result.classes)

        file_records.append({
            "repository_id": repository_id,
            "path": rel_path,
            "language": result.language,
            "ast_hash": result.content_hash,
            "line_count": result.line_count,
            "functions": json.dumps([f.name for f in result.functions]),
            "classes": json.dumps([c.name for c in result.classes]),
            "imports": json.dumps([i.module for i in result.imports]),
            "routes": json.dumps([{"path": r.path, "method": r.method} for r in result.routes]),
            "is_test_file": any(
                p in rel_path for p in ["test_", "_test.", ".test.", ".spec.", "/tests/", "/test/"]
            ),
        })

    async with get_session() as db:
        # Clear old records for this repository
        await db.execute(delete(RepositoryFile).where(RepositoryFile.repository_id == repository_id))
        await db.execute(delete(DependencyEdge).where(DependencyEdge.repository_id == repository_id))

        # Insert new records in batches
        batch_size = 100
        for i in range(0, len(file_records), batch_size):
            batch = file_records[i:i + batch_size]
            db.add_all([RepositoryFile(**r) for r in batch])
            await db.flush()

        for i in range(0, len(edge_records), batch_size):
            batch = edge_records[i:i + batch_size]
            db.add_all([DependencyEdge(**r) for r in batch])
            await db.flush()

    return {
        "files": len(file_records),
        "functions": total_functions,
        "classes": total_classes,
    }


async def _generate_and_store_embeddings(
    repository_id: str,
    parse_results: list[Any],
    repo_path: Path,
) -> None:
    """Generate embeddings for code chunks and store in Qdrant."""
    try:
        from app.utils.qdrant_client import get_qdrant_client
        from app.core.config import get_settings
        settings = get_settings()
        qdrant = get_qdrant_client()

        # Use sentence transformers for local embeddings
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.sentence_transformer_model)

        points = []
        for result in parse_results[:500]:  # Limit to first 500 files
            if result.error or not result.functions:
                continue

            try:
                rel_path = str(Path(result.file_path).relative_to(repo_path))
            except ValueError:
                rel_path = result.file_path

            # Embed each function
            for fn in result.functions[:20]:  # Max 20 functions per file
                text = f"function {fn.name} in {rel_path} language:{result.language}"
                embedding = model.encode(text).tolist()

                import uuid
                points.append({
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "payload": {
                        "repository_id": repository_id,
                        "file_path": rel_path,
                        "language": result.language,
                        "function_name": fn.name,
                        "content": text,
                        "type": "function",
                    },
                })

        if points:
            qdrant.upsert(
                collection_name=settings.qdrant_collection_functions,
                points=points,
            )
            logger.info("Embeddings stored in Qdrant", count=len(points))

    except Exception as e:
        logger.warning("Embedding generation failed (non-fatal)", error=str(e))


async def _update_repo_status(
    repository_id: str,
    status: str,
    error: str | None = None,
    stats: dict[str, int] | None = None,
) -> None:
    """Update repository indexing status in the database."""
    from sqlalchemy import update
    from datetime import datetime, timezone
    from app.database.session import get_session
    from app.models.repository import Repository

    update_values: dict[str, Any] = {
        "index_status": status,
        "is_indexed": status == "indexed",
        "index_error": error,
    }
    if stats:
        update_values.update({
            "total_files": stats.get("files", 0),
            "total_functions": stats.get("functions", 0),
            "total_classes": stats.get("classes", 0),
            "indexed_at": datetime.now(tz=timezone.utc).isoformat(),
        })

    async with get_session() as db:
        await db.execute(
            update(Repository).where(Repository.id == repository_id).values(**update_values)
        )


@celery_app.task(
    name="app.tasks.indexing.cleanup_stale_repos",
    queue="indexing",
)
def cleanup_stale_repos() -> dict[str, int]:
    """Periodic task: remove cloned repositories that haven't been accessed recently."""
    storage_path = settings.repo_storage_path
    removed = 0

    if not storage_path.exists():
        return {"removed": 0}

    for repo_dir in storage_path.iterdir():
        if not repo_dir.is_dir():
            continue
        # Remove if not accessed in 7 days
        mtime = repo_dir.stat().st_mtime
        age_days = (time.time() - mtime) / 86400
        if age_days > 7:
            shutil.rmtree(repo_dir, ignore_errors=True)
            removed += 1
            logger.info("Removed stale repository", path=str(repo_dir), age_days=round(age_days, 1))

    return {"removed": removed}
