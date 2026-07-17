"""TestPilot AI — Pull Request Database Repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pull_request import PullRequest
from app.repositories.base_repo import BaseRepository


class PullRequestRepository(BaseRepository[PullRequest]):
    """Data access layer for Pull Request records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PullRequest)

    async def get_by_pr_number(self, repository_id: str, pr_number: int) -> PullRequest | None:
        """Fetch a Pull Request by repository ID and PR number."""
        result = await self.session.execute(
            select(PullRequest).where(
                PullRequest.repository_id == repository_id,
                PullRequest.pr_number == pr_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_github_pr_id(self, github_pr_id: str) -> PullRequest | None:
        """Fetch a PR by its numeric GitHub PR ID."""
        result = await self.session.execute(
            select(PullRequest).where(PullRequest.github_pr_id == github_pr_id)
        )
        return result.scalar_one_or_none()

    async def get_prs_for_repository(
        self,
        repository_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[PullRequest]:
        """Fetch all Pull Requests for a repository."""
        result = await self.session.execute(
            select(PullRequest)
            .where(PullRequest.repository_id == repository_id)
            .order_by(PullRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
