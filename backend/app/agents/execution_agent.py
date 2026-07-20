"""TestPilot AI — Execution Agent.

Runs the repository's test suite (and any generated tests) in a subprocess.
Collects coverage, logs, timing, and failure details.

Supports: pytest, jest, go test, maven/junit.
"""

from __future__ import annotations

import contextlib
import json
import subprocess
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from app.agents.state import AgentState, TestExecutionResult
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def execution_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: execute the test suite.

    Writes generated tests to temp files, runs the appropriate test runner,
    and collects results including coverage.

    Args:
        state: Current AgentState with generated_tests.

    Returns:
        Partial state with execution_results.
    """
    start_time = time.monotonic()
    logger.info("Execution agent started", pr_id=state.get("pr_id"))

    try:
        repo_path = settings.repo_storage_path / state["repository_id"]

        # Write generated tests to disk
        generated_tests = state.get("generated_tests", [])
        written_files = _write_generated_tests(repo_path, generated_tests)

        # Detect test runner
        runner = _detect_test_runner(repo_path)

        # Execute tests
        result = _run_tests(repo_path, runner, timeout=settings.test_execution_timeout_seconds)

        # Cleanup generated test files
        for f in written_files:
            with contextlib.suppress(OSError):
                f.unlink(missing_ok=True)

        duration = time.monotonic() - start_time
        logger.info(
            "Execution agent completed",
            runner=runner,
            status=result["status"],
            total=result["total"],
            passed=result["passed"],
            failed=result["failed"],
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("execution_agent")

        return {
            "execution_results": result,
            "completed_agents": completed,
            "current_agent": "execution_agent",
        }

    except Exception as e:
        logger.exception("Execution agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"execution_agent: {e}")
        return {
            "errors": errors,
            "execution_results": TestExecutionResult(
                runner="unknown",
                status="error",
                total=0,
                passed=0,
                failed=0,
                skipped=0,
                duration_seconds=0.0,
                coverage_percentage=None,
                failed_tests=[],
                logs=str(e),
            ),
        }


def _write_generated_tests(
    repo_path: Path,
    generated_tests: Sequence[Mapping[str, Any]],
) -> list[Path]:
    """Write generated tests to temporary files in the repository."""
    written = []
    for test in generated_tests:
        test_path = repo_path / test["test_file_path"]
        test_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            test_path.write_text(test["content"])
            written.append(test_path)
            logger.debug("Written generated test", path=str(test_path))
        except OSError as e:
            logger.warning("Could not write generated test", path=str(test_path), error=str(e))
    return written


def _detect_test_runner(repo_path: Path) -> str:
    """Detect the primary test runner from project files."""
    if (repo_path / "pytest.ini").exists() or (repo_path / "pyproject.toml").exists():
        return "pytest"
    if (repo_path / "package.json").exists():
        pkg = json.loads((repo_path / "package.json").read_text())
        scripts = pkg.get("scripts", {})
        if "jest" in str(scripts) or (repo_path / "jest.config.js").exists():
            return "jest"
    if (repo_path / "pom.xml").exists():
        return "maven"
    if (repo_path / "go.mod").exists():
        return "go_test"
    return "pytest"  # Default


def _run_tests(
    repo_path: Path,
    runner: str,
    timeout: int = 300,
) -> TestExecutionResult:
    """Execute the test suite using the detected runner.

    Args:
        repo_path: Absolute path to the repository.
        runner: Test runner identifier.
        timeout: Maximum execution time in seconds.

    Returns:
        TestExecutionResult with parsed results.
    """
    commands = {
        "pytest": [
            "python",
            "-m",
            "pytest",
            "--json-report",
            "--json-report-file=/tmp/testpilot_report.json",
            "--cov=.",
            "--cov-report=json:/tmp/testpilot_coverage.json",
            "-v",
            "--tb=short",
            "--no-header",
        ],
        "jest": [
            "npx",
            "jest",
            "--json",
            "--outputFile=/tmp/testpilot_jest.json",
            "--coverage",
            "--coverageReporters=json",
        ],
        "go_test": ["go", "test", "./...", "-v", "-cover"],
        "maven": ["mvn", "test", "-q"],
    }

    cmd = commands.get(runner, commands["pytest"])
    logger.info("Running tests", runner=runner, cwd=str(repo_path))

    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = time.monotonic() - start
        logs = proc.stdout + proc.stderr

        # Parse results
        return _parse_pytest_results(proc, duration, logs)

    except subprocess.TimeoutExpired:
        logger.warning("Test execution timed out", runner=runner, timeout=timeout)
        return TestExecutionResult(
            runner=runner,
            status="error",
            total=0,
            passed=0,
            failed=0,
            skipped=0,
            duration_seconds=float(timeout),
            coverage_percentage=None,
            failed_tests=[],
            logs=f"Execution timed out after {timeout}s",
        )
    except FileNotFoundError as e:
        logger.warning("Test runner not found", runner=runner, error=str(e))
        return TestExecutionResult(
            runner=runner,
            status="error",
            total=0,
            passed=0,
            failed=0,
            skipped=0,
            duration_seconds=0.0,
            coverage_percentage=None,
            failed_tests=[],
            logs=f"Runner not found: {e}",
        )


def _parse_pytest_results(
    proc: subprocess.CompletedProcess[str],
    duration: float,
    logs: str,
) -> TestExecutionResult:
    """Parse pytest JSON report output."""
    # Try to read JSON report
    report_path = Path("/tmp/testpilot_report.json")
    failed_tests = []
    total = passed = failed = skipped = 0

    if report_path.exists():
        try:
            report = json.loads(report_path.read_text())
            summary = report.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            skipped = summary.get("skipped", 0)

            for test in report.get("tests", []):
                if test.get("outcome") == "failed":
                    failed_tests.append(
                        {
                            "name": test.get("nodeid", "unknown"),
                            "message": test.get("call", {}).get("longrepr", ""),
                            "duration": test.get("call", {}).get("duration", 0),
                        }
                    )
        except (json.JSONDecodeError, KeyError):
            pass

    # Parse coverage
    coverage_pct = None
    coverage_path = Path("/tmp/testpilot_coverage.json")
    if coverage_path.exists():
        try:
            cov_data = json.loads(coverage_path.read_text())
            total_stmts = cov_data.get("totals", {}).get("num_statements", 0)
            covered = cov_data.get("totals", {}).get("covered_lines", 0)
            if total_stmts > 0:
                coverage_pct = round(covered / total_stmts * 100, 2)
        except (json.JSONDecodeError, KeyError, ZeroDivisionError):
            pass

    status = "passed" if proc.returncode == 0 else "failed"

    return TestExecutionResult(
        runner="pytest",
        status=status,
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration_seconds=round(duration, 2),
        coverage_percentage=coverage_pct,
        failed_tests=failed_tests,
        logs=logs[-10000:],  # Last 10KB of logs
    )
