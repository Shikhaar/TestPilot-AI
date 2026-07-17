"""TestPilot AI — User ORM Model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base_class import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.repository import Repository


class User(Base, UUIDMixin, TimestampMixin):
    """Represents an authenticated user (via GitHub OAuth).

    Attributes:
        github_id: The user's GitHub numeric ID.
        username: GitHub username (login).
        email: GitHub primary email address.
        name: GitHub display name.
        avatar_url: URL to the user's GitHub avatar.
        github_access_token: OAuth access token for GitHub API calls.
        role: User role: 'admin' | 'member' | 'viewer'.
        is_active: Whether the account is active.
        repositories: Repositories connected by this user.
    """

    __tablename__ = "users"

    github_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    repositories: Mapped[list[Repository]] = relationship(
        "Repository",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username}>"
