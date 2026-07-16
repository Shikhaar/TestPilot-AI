"""
TestPilot AI — SQLAlchemy Async Session Factory.

Provides async database session management using SQLAlchemy 2 with asyncpg.
Follows the Unit of Work pattern via FastAPI dependency injection.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# ==============================================================================
# Engine
# ==============================================================================

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "application_name": settings.app_name,
            "jit": "off",  # Disable JIT for better pg performance on short queries
        }
    },
)

# ==============================================================================
# Session Factory
# ==============================================================================

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ==============================================================================
# Session Dependency
# ==============================================================================


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides a database session per request.

    Opens a session, yields it, and automatically rolls back on exception
    or commits on success. Always closes the session afterwards.

    Yields:
        AsyncSession: An active SQLAlchemy async session.

    Example:
        >>> @router.get("/repos")
        ... async def list_repos(db: AsyncSession = Depends(get_db_session)):
        ...     ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ==============================================================================
# Context Manager (for use outside of FastAPI request cycle)
# ==============================================================================


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for database sessions.

    Use this in Celery tasks or other contexts outside the FastAPI
    request/response cycle.

    Yields:
        AsyncSession: An active SQLAlchemy async session.

    Example:
        >>> async with get_session() as db:
        ...     repos = await db.execute(select(Repository))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Database session error, rolling back")
            raise
        finally:
            await session.close()
