"""TestPilot AI — User Database Repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access layer for User records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_github_id(self, github_id: str) -> User | None:
        """Fetch user by GitHub profile ID."""
        result = await self.session.execute(select(User).where(User.github_id == github_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        """Fetch user by GitHub username."""
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by email."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
