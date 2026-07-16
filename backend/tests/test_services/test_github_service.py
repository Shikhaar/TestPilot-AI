"""TestPilot AI — GitHub Service Tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.github_service import GitHubService


@pytest.fixture
def github_service() -> GitHubService:
    """GitHub service instance with mock integration."""
    service = GitHubService()
    # Stub the App integration to avoid authenticating during unit tests
    service._integration = MagicMock()
    return service


def test_detect_language_from_path(github_service: GitHubService) -> None:
    """Test that file extensions map to correct languages."""
    assert github_service._detect_language_from_path("app/main.py") == "Python"
    assert github_service._detect_language_from_path("src/index.ts") == "TypeScript"
    assert github_service._detect_language_from_path("src/App.jsx") == "JavaScript"
    assert github_service._detect_language_from_path("main.go") == "Go"
    assert github_service._detect_language_from_path("README.md") is None
