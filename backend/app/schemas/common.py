"""
TestPilot AI — Common Pydantic Schemas.

Provides shared response envelopes, pagination, and error schemas
used across all API endpoints.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class BaseSchema(BaseModel):
    """Base schema with common configuration.

    Uses model_config to:
    - Allow population from ORM model attributes (from_attributes)
    - Use enum values in serialization
    - Validate assignment after model creation
    """

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate SQL offset from page number."""
        return (self.page - 1) * self.page_size


class PaginatedResponse[T](BaseModel):
    """Generic paginated response envelope."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> PaginatedResponse[T]:
        """Factory method to create a paginated response.

        Args:
            items: The items on the current page.
            total: Total number of items across all pages.
            page: Current page number.
            page_size: Items per page.

        Returns:
            A constructed PaginatedResponse.
        """
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


class APIResponse[T](BaseModel):
    """Standard API response envelope."""

    success: bool = True
    data: T | None = None
    message: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error: str
    detail: str | None = None
    request_id: str | None = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    environment: str
    services: dict[str, str] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Response for async task submissions."""

    task_id: str
    status: str = "queued"
    message: str | None = None
    estimated_duration_seconds: int | None = None
