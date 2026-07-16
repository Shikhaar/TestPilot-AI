"""TestPilot AI — Test Discovery Agent.

Scans the repository to find existing test files, understand test coverage,
and identify which modules lack adequate test coverage.

Supports: pytest, jest, junit, go test, nunit, mocha, rspec.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from app.agents.state import AgentState, TestFile
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Patterns to identify test frameworks
FRAMEWORK_PATTERNS = {
    "pytest": [r"import pytest", r"from pytest", r"def test_", r"@pytest"],
    "jest": [r"describe\(", r"it\(", r"test\(", r"expect\(", r"jest\."],
    "junit": [r"@Test", r"@RunWith", r"import org\.junit"],
    "go_test": [r"func Test", r"testing\.T"],
    "mocha": [r"describe\(", r"it\(", r"require\('mocha'\)"],
    "rspec": [r"describe ", r"it ", r"expect\(", r"require 'spec_helper'"],
}

TEST_FILE_PATTERNS = [
    r"test_.*\.py$",
    r".*_test\.py$",
    r".*\.test\.(js|ts|jsx|tsx)$",
    r".*\.spec\.(js|ts|jsx|tsx)$",
    r".*Test\.java$",
    r".*_test\.go$",
    r".*_test\.rb$",
    r".*Tests?\.(cs|java)$",
]


def test_discovery_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: discover existing tests in the repository.

    Scans the cloned repository for test files, identifies their framework,
    counts test cases, and maps test files to the source modules they cover.

    Args:
        state: Current AgentState.

    Returns:
        Partial state with existing_tests, uncovered_modules, coverage_gaps.
    """
    start_time = time.monotonic()
    logger.info("Test discovery agent started", repo_id=state.get("repository_id"))

    try:
        repo_path = settings.repo_storage_path / state["repository_id"]

        test_files = _discover_test_files(repo_path)
        uncovered = _find_uncovered_modules(state, test_files)

        duration = time.monotonic() - start_time
        logger.info(
            "Test discovery agent completed",
            test_files=len(test_files),
            uncovered_modules=len(uncovered),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("test_discovery_agent")

        return {
            "existing_tests": test_files,
            "uncovered_modules": uncovered,
            "coverage_gaps": uncovered[:20],
            "completed_agents": completed,
            "current_agent": "test_discovery_agent",
        }

    except Exception as e:
        logger.exception("Test discovery agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"test_discovery_agent: {e}")
        return {"errors": errors, "existing_tests": [], "uncovered_modules": []}


def _discover_test_files(repo_path: Path) -> list[TestFile]:
    """Scan a repository for test files."""
    if not repo_path.exists():
        return []

    test_files = []
    compiled_patterns = [re.compile(p) for p in TEST_FILE_PATTERNS]

    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        # Skip ignored directories
        if any(part in settings.ignored_directories for part in file_path.parts):
            continue

        relative_path = str(file_path.relative_to(repo_path))

        # Check if this matches any test file pattern
        if not any(p.search(relative_path) for p in compiled_patterns):
            continue

        try:
            content = file_path.read_text(errors="replace")
        except OSError:
            continue

        framework = _detect_framework(content, relative_path)
        test_names = _extract_test_names(content, framework)
        covers = _infer_covered_modules(relative_path, content)

        test_files.append(
            TestFile(
                path=relative_path,
                framework=framework,
                test_count=len(test_names),
                test_names=test_names[:50],  # Cap at 50
                covers_modules=covers,
            )
        )

    return test_files


def _detect_framework(content: str, file_path: str) -> str:
    """Detect the test framework used in a file."""
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        if any(re.search(p, content) for p in patterns):
            return framework

    # Fallback to extension-based detection
    if file_path.endswith(".py"):
        return "pytest"
    if file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
        return "jest"
    if file_path.endswith(".java"):
        return "junit"
    if file_path.endswith("_test.go"):
        return "go_test"
    return "unknown"


def _extract_test_names(content: str, framework: str) -> list[str]:
    """Extract test function/method names from file content."""
    patterns_by_framework = {
        "pytest": r"def (test_\w+)",
        "jest": r"(?:it|test)\(['\"]([^'\"]+)['\"]",
        "junit": r"public void (\w+)\(\)",
        "go_test": r"func (Test\w+)\(",
        "mocha": r"(?:it|describe)\(['\"]([^'\"]+)['\"]",
        "rspec": r"it ['\"]([^'\"]+)['\"]",
    }
    pattern = patterns_by_framework.get(framework)
    if not pattern:
        return []
    return re.findall(pattern, content)


def _infer_covered_modules(test_path: str, content: str) -> list[str]:
    """Infer which source modules a test file covers."""
    covered = []
    # From test file naming convention
    name = Path(test_path).stem
    source_name = name.replace("test_", "").replace("_test", "")
    if source_name:
        covered.append(source_name)
    # From import statements
    imports = re.findall(r"(?:from|import)\s+([\w.]+)", content)
    for imp in imports:
        if not imp.startswith(("test", "pytest", "jest", "unittest")):
            covered.append(imp.split(".")[-1])
    return list(set(covered))[:10]


def _find_uncovered_modules(state: AgentState, test_files: list[TestFile]) -> list[str]:
    """Find changed modules that lack test coverage."""
    covered_modules: set[str] = set()
    for tf in test_files:
        covered_modules.update(tf["covers_modules"])

    uncovered = []
    for node in state.get("changed_nodes", []):
        module = Path(node["file_path"]).stem
        if module not in covered_modules:
            uncovered.append(node["file_path"])

    return list(set(uncovered))
