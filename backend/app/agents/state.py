"""
TestPilot AI — LangGraph Agent State.

Defines the shared state TypedDict that flows through the entire
LangGraph multi-agent pipeline. Every agent reads from and writes to this
state object. Type safety is enforced via TypedDict annotations.
"""

from __future__ import annotations

from typing import Any, TypedDict


class ChangedFile(TypedDict):
    """A file changed in the PR diff."""
    path: str
    status: str  # 'added' | 'modified' | 'deleted' | 'renamed'
    additions: int
    deletions: int
    old_path: str | None


class CodeNode(TypedDict):
    """A code symbol (function, class, route) identified in the diff."""
    name: str
    type: str  # 'function' | 'class' | 'route' | 'model'
    file_path: str
    line_start: int
    line_end: int
    language: str


class TestFile(TypedDict):
    """An existing test file discovered in the repository."""
    path: str
    framework: str
    test_count: int
    test_names: list[str]
    covers_modules: list[str]


class GeneratedTest(TypedDict):
    """An AI-generated test case."""
    function_name: str
    class_name: str | None
    file_path: str
    test_file_path: str
    content: str
    test_type: str
    test_framework: str
    language: str


class TestExecutionResult(TypedDict):
    """Result of running a test suite."""
    runner: str
    status: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    coverage_percentage: float | None
    failed_tests: list[dict[str, Any]]
    logs: str


class FailureAnalysis(TypedDict):
    """AI analysis of a test failure."""
    test_name: str
    failure_message: str
    root_cause: str
    affected_code_path: str | None
    suggested_fix: str
    confidence: float


class RiskScore(TypedDict):
    """Risk assessment for the PR."""
    level: str  # 'low' | 'medium' | 'high' | 'critical'
    score: float  # 0.0 - 10.0
    factors: list[str]
    historical_context: str | None


class PRReview(TypedDict):
    """The complete AI-generated PR review."""
    risk_level: str
    risk_score: float
    summary: str
    risk_factors: list[dict[str, str]]
    action_items: list[str]
    historical_warnings: list[str]
    full_review_body: str


class AgentState(TypedDict, total=False):
    """The shared state object for the LangGraph agent pipeline.

    This TypedDict is the single source of truth flowing between all agents.
    Each agent reads its required inputs and writes its outputs back here.

    Required fields (set at pipeline start):
        pr_id: Internal TestPilot PR UUID.
        repository_id: Internal Repository UUID.
        repo_full_name: GitHub full name (e.g., 'owner/repo').
        pr_number: GitHub PR number.
        head_sha: HEAD commit SHA.
        base_sha: Base commit SHA.
        installation_id: GitHub App installation ID.

    Populated by agents (in pipeline order):
        diff: Raw PR diff data.
        changed_files: Parsed list of changed files.
        changed_nodes: Code symbols identified in the diff.
        dependency_graph_edges: Serialized dependency graph edges.
        affected_modules: Modules affected by the changes.
        affected_services: High-level services affected.
        affected_apis: API endpoints affected.
        existing_tests: Discovered test files.
        uncovered_modules: Modules lacking test coverage.
        generated_tests: AI-generated test cases.
        execution_results: Test suite execution results.
        failure_analyses: AI analyses of test failures.
        risk_score: PR risk assessment.
        review: Final AI-generated PR review.

    Control flow:
        errors: List of error messages (non-fatal).
        retry_count: Current retry count for the active agent.
        should_stop: Whether the pipeline should halt early.
        current_agent: Name of the currently executing agent.
        completed_agents: List of successfully completed agent names.
    """

    # ---- Input (set at pipeline start) ----
    pr_id: str
    repository_id: str
    repo_full_name: str
    pr_number: int
    head_sha: str
    base_sha: str
    installation_id: str | None

    # ---- Diff Agent outputs ----
    diff: dict[str, Any]
    changed_files: list[ChangedFile]
    changed_nodes: list[CodeNode]

    # ---- Dependency Agent outputs ----
    dependency_graph_edges: list[dict[str, str]]

    # ---- Impact Agent outputs ----
    affected_modules: list[str]
    affected_services: list[str]
    affected_apis: list[str]

    # ---- Search Agent outputs ----
    retrieved_context: list[dict[str, Any]]

    # ---- Test Discovery Agent outputs ----
    existing_tests: list[TestFile]
    uncovered_modules: list[str]
    coverage_gaps: list[str]

    # ---- Test Generator Agent outputs ----
    generated_tests: list[GeneratedTest]

    # ---- Execution Agent outputs ----
    execution_results: TestExecutionResult

    # ---- Failure Analysis Agent outputs ----
    failure_analyses: list[FailureAnalysis]

    # ---- Review Agent outputs ----
    risk_score: RiskScore
    review: PRReview

    # ---- Documentation Agent outputs ----
    documentation_updates: list[dict[str, str]]

    # ---- Control flow ----
    errors: list[str]
    retry_count: int
    should_stop: bool
    current_agent: str
    completed_agents: list[str]
