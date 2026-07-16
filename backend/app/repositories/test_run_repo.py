"""TestPilot AI — Test Run Database Repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test_run import TestRun
from app.repositories.base import BaseRepository


class TestRunRepository(BaseRepository[TestRun]):
    """Data access layer for Test Run records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TestRun)

    async def get_runs_for_pr(self, pull_request_id: str) -> Sequence[TestRun]:
        """Fetch all test runs associated with a Pull Request."""
        result = await self.session.execute(
            select(TestRun)
            .where(TestRun.pull_request_id == pull_request_id)
            .order_by(TestRun.created_at.desc())
        )
        return result.scalars().all()

    async def get_latest_run_for_pr(self, pull_request_id: str) -> TestRun | None:
        """Fetch the most recent test run for a Pull Request."""
        result = await self.session.execute(
            select(TestRun)
            .where(TestRun.pull_request_id == pull_request_id)
            .order_by(TestRun.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
