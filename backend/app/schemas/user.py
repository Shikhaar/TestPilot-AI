"""TestPilot AI — User Pydantic Schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from app.schemas.common import BaseSchema


class UserRole(StrEnum):
    """User role enum."""

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class UserResponse(BaseSchema):
    """Public user profile response."""

    id: str
    github_id: str
    username: str
    email: str | None
    name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(BaseSchema):
    """JWT token response after successful authentication."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")
    user: UserResponse


class GitHubCallbackRequest(BaseSchema):
    """GitHub OAuth callback request body."""

    code: str = Field(..., description="GitHub OAuth authorization code")
    state: str | None = Field(default=None, description="OAuth state parameter")


class RefreshTokenRequest(BaseSchema):
    """Request to refresh an access token."""

    refresh_token: str
