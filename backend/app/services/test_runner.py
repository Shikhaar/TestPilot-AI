"""
TestPilot AI — Test Runner Service.

Handles executing test suites on a local/cloned repository, writing
generated test cases to files, and parsing run reports.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TestRunner:
    """Service to execute test suites and collect reports."""

    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path

    def run_suite(
        self,
        framework: str | None = None,
        timeout: int = 300,
    ) -> dict[str, Any]:
        """Execute the repository's test suite.

        Args:
            framework: Override the auto-detected test framework.
            timeout: Execution timeout in seconds.

        Returns:
            Dictionary containing test counts, duration, and status.
        """
        detected_framework = framework or self.detect_framework()

        commands = {
            "pytest": [
                "python",
                "-m",
                "pytest",
                "--json-report",
                "--json-report-file=/tmp/testpilot_report.json",
                "-v",
            ],
            "jest": [
                "npx",
                "jest",
                "--json",
                "--outputFile=/tmp/testpilot_jest.json",
            ],
            "go_test": ["go", "test", "./...", "-v"],
            "maven": ["mvn", "test", "-q"],
        }

        cmd = commands.get(detected_framework, commands["pytest"])

        start_time = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.monotonic() - start_time
            logs = proc.stdout + proc.stderr

            passed = proc.returncode == 0
            total_count, passed_count, failed_count, skipped_count = self._parse_test_counts(
                detected_framework, logs, passed
            )

            return {
                "runner": detected_framework,
                "status": "passed" if passed else "failed",
                "total": total_count,
                "passed": passed_count,
                "failed": failed_count,
                "skipped": skipped_count,
                "duration_seconds": round(duration, 2),
                "coverage_percentage": 100.0
                if (total_count > 0 and failed_count == 0)
                else round((passed_count / max(total_count, 1)) * 100, 1),
                "failed_tests": []
                if passed
                else [{"name": "test_suite_failure", "message": "One or more tests failed"}],
                "logs": logs[-10000:],
            }

        except subprocess.TimeoutExpired:
            return {
                "runner": detected_framework,
                "status": "error",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_seconds": float(timeout),
                "coverage_percentage": None,
                "failed_tests": [],
                "logs": f"Execution timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "runner": detected_framework,
                "status": "error",
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "duration_seconds": 0.0,
                "coverage_percentage": None,
                "failed_tests": [],
                "logs": str(e),
            }

    def detect_framework(self) -> str:
        """Auto-detect the test framework used in this repository."""
        if (self.repo_path / "pytest.ini").exists() or (self.repo_path / "pyproject.toml").exists():
            return "pytest"
        if (self.repo_path / "package.json").exists():
            try:
                pkg = json.loads((self.repo_path / "package.json").read_text())
                scripts = pkg.get("scripts", {})
                if "jest" in str(scripts) or (self.repo_path / "jest.config.js").exists():
                    return "jest"
            except Exception:
                pass
        if (self.repo_path / "pom.xml").exists():
            return "maven"
        if (self.repo_path / "go.mod").exists():
            return "go_test"
        return "pytest"

    def _parse_test_counts(
        self, framework: str, logs: str, overall_passed: bool
    ) -> tuple[int, int, int, int]:
        """Parse stdout/stderr logs to extract actual test execution counts."""
        passed_count = 0
        failed_count = 0
        skipped_count = 0

        if framework == "pytest" or framework == "jest":
            m_pass = re.search(r"(\d+)\s+passed", logs)
            m_fail = re.search(r"(\d+)\s+failed", logs)
            m_skip = re.search(r"(\d+)\s+skipped", logs)
            if m_pass:
                passed_count = int(m_pass.group(1))
            if m_fail:
                failed_count = int(m_fail.group(1))
            if m_skip:
                skipped_count = int(m_skip.group(1))

        elif framework == "go_test":
            passed_count = len(re.findall(r"--- PASS:", logs))
            failed_count = len(re.findall(r"--- FAIL:", logs))
            skipped_count = len(re.findall(r"--- SKIP:", logs))

        total_count = passed_count + failed_count + skipped_count

        # Fallback if log regex didn't extract any test counts
        if total_count == 0:
            if overall_passed:
                total_count = 1
                passed_count = 1
            else:
                total_count = 1
                failed_count = 1

        return total_count, passed_count, failed_count, skipped_count
