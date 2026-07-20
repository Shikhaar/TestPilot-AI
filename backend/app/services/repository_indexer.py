"""
TestPilot AI — Repository Indexer Service.

Orchestrates cloning repositories, parsing source code AST,
building the dependency graph, generating vector embeddings, and
persisting index metadata to databases.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.dependency_graph import DependencyEdge
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.services.ast_parser import ASTParser
from app.services.dependency_graph_builder import DependencyGraphBuilder
from app.services.embedding_service import get_embedding_service
from app.utils.qdrant_client import get_qdrant_client

logger = get_logger(__name__)
settings = get_settings()


class RepositoryIndexer:
    """Service responsible for indexing a code repository."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.parser = ASTParser()
        self.embedding_service = get_embedding_service()

    async def index(
        self,
        repository: Repository,
        repo_path: Path,
        force: bool = False,
    ) -> dict[str, int]:
        """Perform full indexing pipeline for the repository.

        Args:
            repository: The Repository model instance.
            repo_path: The local absolute path where the repository is cloned.
            force: Whether to overwrite existing indexes.

        Returns:
            Dictionary with statistics: files, functions, classes indexed.
        """
        logger.info("Indexing codebase", repo=repository.full_name, path=str(repo_path))

        # 1. Parse all files in the directory
        parse_results = self.parser.parse_directory(repo_path)

        # 2. Build dependency graph
        graph_builder = DependencyGraphBuilder(repo_path)
        graph_builder.build(parse_results)
        edge_records = graph_builder.to_edge_records(repository.id)

        # 3. Clear old Postgres records if force/reindex
        await self.db.execute(
            delete(RepositoryFile).where(RepositoryFile.repository_id == repository.id)
        )
        await self.db.execute(
            delete(DependencyEdge).where(DependencyEdge.repository_id == repository.id)
        )

        # 4. Persist files and functions to DB
        file_count = 0
        function_count = 0
        class_count = 0

        for res in parse_results:
            if res.error:
                continue

            try:
                rel_path = str(Path(res.file_path).relative_to(repo_path))
            except ValueError:
                rel_path = res.file_path

            db_file = RepositoryFile(
                repository_id=repository.id,
                path=rel_path,
                language=res.language,
                ast_hash=res.content_hash,
                line_count=res.line_count,
                functions=json.dumps([f.name for f in res.functions]),
                classes=json.dumps([c.name for c in res.classes]),
                imports=json.dumps([i.module for i in res.imports]),
                routes=json.dumps([{"path": r.path, "method": r.method} for r in res.routes]),
                is_test_file=any(
                    p in rel_path
                    for p in ["test_", "_test.", ".test.", ".spec.", "/tests/", "/test/"]
                ),
            )
            self.db.add(db_file)
            file_count += 1
            function_count += len(res.functions)
            class_count += len(res.classes)

        # Bulk insert dependency edges
        for edge in edge_records:
            self.db.add(DependencyEdge(**edge))

        await self.db.flush()

        # 5. Generate embeddings and upload to Qdrant
        await self._index_embeddings_in_qdrant(repository.id, parse_results, repo_path)

        return {
            "files": file_count,
            "functions": function_count,
            "classes": class_count,
            "edges": len(edge_records),
        }

    async def _index_embeddings_in_qdrant(
        self,
        repository_id: str,
        parse_results: list[Any],
        repo_path: Path,
    ) -> None:
        """Create embeddings for functions and insert into Qdrant store."""
        try:
            qdrant = get_qdrant_client()
            points = []

            for res in parse_results[:200]:  # Limit first 200 files for local memory safety
                if res.error or not res.functions:
                    continue

                try:
                    rel_path = str(Path(res.file_path).relative_to(repo_path))
                except ValueError:
                    rel_path = res.file_path

                for fn in res.functions[:15]:  # Max 15 functions per file
                    chunk_text = f"function {fn.name} in {rel_path} language:{res.language}"
                    # Generate embedding
                    embedding = self.embedding_service.generate_embedding(chunk_text)

                    import uuid

                    points.append(
                        {
                            "id": str(uuid.uuid4()),
                            "vector": embedding,
                            "payload": {
                                "repository_id": repository_id,
                                "file_path": rel_path,
                                "language": res.language,
                                "function_name": fn.name,
                                "content": chunk_text,
                                "type": "function",
                            },
                        }
                    )

            if points:
                qdrant.upsert(
                    collection_name=settings.qdrant_collection_repository_chunks,
                    points=points,  # type: ignore[arg-type]
                )
                logger.info("Uploaded code embeddings to Qdrant", count=len(points))

        except Exception as e:
            logger.warning("Failed to store Qdrant embeddings (non-fatal)", error=str(e))
