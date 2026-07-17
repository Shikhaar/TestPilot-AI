"""TestPilot AI — Repository Data Access Repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.repository import Repository
from app.repositories.base_repo import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    """Data access layer for Repository records."""

    def __init__(self, session: object) -> None:
        super().__init__(session, Repository)  # type: ignore[arg-type]

    async def get_by_full_name(self, full_name: str) -> Repository | None:
        """Fetch a repository by its GitHub full name.

        Args:
            full_name: GitHub full name (e.g., 'owner/repo').

        Returns:
            The Repository instance or None.
        """
        result = await self.session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        return result.scalar_one_or_none()

    async def get_by_github_id(self, github_repo_id: str) -> Repository | None:
        """Fetch a repository by its GitHub numeric ID."""
        result = await self.session.execute(
            select(Repository).where(Repository.github_repo_id == github_repo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_owner(
        self,
        owner_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Repository]:
        """Fetch all repositories for a given user.

        Args:
            owner_id: The user's UUID.
            offset: Pagination offset.
            limit: Pagination limit.

        Returns:
            Sequence of Repository instances.
        """
        result = await self.session.execute(
            select(Repository)
            .where(Repository.owner_id == owner_id)
            .order_by(Repository.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_indexed_repositories(self) -> Sequence[Repository]:
        """Fetch all fully indexed repositories."""
        result = await self.session.execute(
            select(Repository).where(Repository.is_indexed.is_(True))
        )
        return result.scalars().all()

    async def update_index_status(
        self,
        repo_id: str,
        status: str,
        error: str | None = None,
    ) -> Repository | None:
        """Update the indexing status of a repository.

        Args:
            repo_id: Repository UUID.
            status: New status string.
            error: Optional error message.

        Returns:
            Updated Repository or None if not found.
        """
        return await self.update(
            repo_id,
            index_status=status,
            is_indexed=(status == "indexed"),
            index_error=error,
        )
