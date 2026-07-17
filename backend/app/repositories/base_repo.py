"""
TestPilot AI — Generic Base Repository.

Implements the Repository pattern with async SQLAlchemy 2.
All model-specific repositories inherit from this base class.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)

logger = get_logger(__name__)


class BaseRepository[ModelT: Base]:
    """Generic async repository providing CRUD operations.

    Type Parameters:
        ModelT: The SQLAlchemy ORM model class.

    Args:
        session: An active SQLAlchemy async session.
        model: The ORM model class to operate on.
    """

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: str) -> ModelT | None:
        """Fetch a single record by primary key.

        Args:
            id: The UUID primary key.

        Returns:
            The model instance or None if not found.
        """
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)  # type: ignore[attr-defined]
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
        order_by: Any = None,
    ) -> Sequence[ModelT]:
        """Fetch all records with optional pagination.

        Args:
            offset: Number of records to skip.
            limit: Maximum records to return.
            order_by: SQLAlchemy column expression for ordering.

        Returns:
            Sequence of model instances.
        """
        stmt = select(self.model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Count total records in the table.

        Returns:
            Total record count.
        """
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()

    async def create(self, **kwargs: Any) -> ModelT:
        """Create and persist a new record.

        Args:
            **kwargs: Column values for the new record.

        Returns:
            The newly created model instance.
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        logger.debug("Created record", model=self.model.__name__, id=instance.id)  # type: ignore[attr-defined]
        return instance

    async def update(self, id: str, **kwargs: Any) -> ModelT | None:
        """Update an existing record by ID.

        Args:
            id: The UUID primary key.
            **kwargs: Column values to update.

        Returns:
            The updated model instance or None if not found.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        logger.debug("Updated record", model=self.model.__name__, id=id)
        return instance

    async def delete(self, id: str) -> bool:
        """Delete a record by ID.

        Args:
            id: The UUID primary key.

        Returns:
            True if deleted, False if not found.
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.flush()
        logger.debug("Deleted record", model=self.model.__name__, id=id)
        return True

    async def bulk_create(self, records: list[dict[str, Any]]) -> list[ModelT]:
        """Bulk create multiple records in one flush.

        Args:
            records: List of column value dictionaries.

        Returns:
            List of created model instances.
        """
        instances = [self.model(**record) for record in records]
        self.session.add_all(instances)
        await self.session.flush()
        return instances
