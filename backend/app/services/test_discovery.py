"""
TestPilot AI — Test Discovery Service.

Identifies test files, framework usages, and test case counts in a codebase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agents.test_discovery_agent import _discover_test_files


class TestDiscovery:
    """Service to discover and analyze tests in a workspace."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path

    def discover(self) -> dict[str, Any]:
        """Scan directory and return structured list of tests.

        Returns:
            Dictionary with counts and test suite statistics.
        """
        test_files = _discover_test_files(self.repo_path)

        frameworks = list(set(tf["framework"] for tf in test_files))
        total_tests = sum(tf["test_count"] for tf in test_files)

        return {
            "total_test_files": len(test_files),
            "total_tests": total_tests,
            "frameworks_detected": frameworks,
            "test_files": [
                {
                    "file_path": tf["path"],
                    "framework": tf["framework"],
                    "test_count": tf["test_count"],
                    "test_names": tf["test_names"],
                    "covers_modules": tf["covers_modules"],
                }
                for tf in test_files
            ],
        }
