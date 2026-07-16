"""TestPilot AI — Pytest Configuration and Fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.database.base import Base
from app.main import app
from app.api.deps import get_db


# ==============================================================================
# Test Settings Override
# ==============================================================================


def get_test_settings() -> Settings:
    """Override settings for test environment."""
    return Settings(
        app_env="test",
        debug=True,
        secret_key="test-secret-key-for-testing-only",
        jwt_secret_key="test-jwt-secret-key",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
        celery_broker_url="memory://",
        celery_result_backend="cache+memory://",
        qdrant_url="http://localhost:6333",
        github_webhook_secret="test-webhook-secret",
        rate_limit_enabled=False,
        openai_api_key="sk-test-placeholder",
        use_local_embeddings=False,
    )


# ==============================================================================
# Database Fixtures
# ==============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create a session-scoped event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create an in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session per test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ==============================================================================
# Application Fixtures
# ==============================================================================


@pytest.fixture
def test_app(db_session: AsyncSession):
    """Create a test FastAPI application with test DB."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_settings] = get_test_settings
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as c:
        yield c


# ==============================================================================
# Model Fixtures
# ==============================================================================


@pytest.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.user import User
    import uuid

    user = User(
        id=str(uuid.uuid4()),
        github_id="12345",
        username="test_user",
        email="test@example.com",
        name="Test User",
        role="member",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def test_repository(db_session: AsyncSession, test_user):
    """Create a test repository."""
    from app.models.repository import Repository
    import uuid

    repo = Repository(
        id=str(uuid.uuid4()),
        owner_id=test_user.id,
        github_repo_id="99999",
        full_name="test-owner/test-repo",
        name="test-repo",
        owner_login="test-owner",
        clone_url="https://github.com/test-owner/test-repo.git",
        default_branch="main",
        index_status="indexed",
        is_indexed=True,
    )
    db_session.add(repo)
    await db_session.flush()
    return repo


@pytest.fixture
async def test_pull_request(db_session: AsyncSession, test_repository):
    """Create a test pull request."""
    from app.models.pull_request import PullRequest
    import uuid

    pr = PullRequest(
        id=str(uuid.uuid4()),
        repository_id=test_repository.id,
        pr_number=42,
        github_pr_id="99998",
        title="Test PR: Add payment service",
        state="open",
        author="test-dev",
        base_branch="main",
        head_branch="feature/payment",
        head_sha="abc123def456",
        base_sha="111222333444",
        analysis_status="pending",
    )
    db_session.add(pr)
    await db_session.flush()
    return pr


@pytest.fixture
def auth_headers(test_user) -> dict[str, str]:
    """Create JWT authentication headers for a test user."""
    from app.core.security import create_access_token
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Mock Fixtures
# ==============================================================================


@pytest.fixture
def mock_github_service():
    """Mock the GitHub service to avoid real API calls."""
    mock = MagicMock()
    mock.get_pull_request.return_value = MagicMock(
        additions=50,
        deletions=20,
        changed_files=3,
        get_files=lambda: [],
    )
    mock.extract_diff_summary.return_value = MagicMock(
        changed_files=[],
        total_additions=50,
        total_deletions=20,
        affected_languages=["Python"],
        changed_functions=[],
        changed_classes=[],
        changed_routes=[],
    )
    return mock


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant client to avoid real vector DB calls."""
    mock = MagicMock()
    mock.search.return_value = []
    mock.upsert.return_value = None
    mock.get_collections.return_value = MagicMock(collections=[])
    return mock
