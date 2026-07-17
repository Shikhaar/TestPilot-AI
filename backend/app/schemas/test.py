"""TestPilot AI — Test Pydantic Schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from app.schemas.common import BaseSchema


class TestFramework(StrEnum):
    PYTEST = "pytest"
    JEST = "jest"
    JUNIT = "junit"
    GO_TEST = "go_test"
    NUNIT = "nunit"
    MOCHA = "mocha"
    RSPEC = "rspec"


class TestType(StrEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    EDGE_CASE = "edge_case"
    NEGATIVE = "negative"
    BOUNDARY = "boundary"
    FAILURE = "failure"
    CONCURRENCY = "concurrency"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    MOCK = "mock"
    PROPERTY_BASED = "property_based"


class TestDiscoverRequest(BaseSchema):
    """Request to discover existing tests in a repository."""

    repository_id: str
    scan_path: str | None = Field(default=None, description="Specific path to scan (optional)")


class TestGenerateRequest(BaseSchema):
    """Request to generate tests for a PR."""

    pr_id: str
    target_functions: list[str] = Field(
        default_factory=list,
        description="Specific functions to generate tests for (empty = all changed)",
    )
    test_types: list[TestType] = Field(
        default_factory=lambda: [TestType.UNIT, TestType.EDGE_CASE, TestType.NEGATIVE],
        description="Types of tests to generate",
    )
    max_tests_per_function: int = Field(default=5, ge=1, le=20)


class TestRunRequest(BaseSchema):
    """Request to execute the test suite."""

    pr_id: str
    repository_id: str
    framework: TestFramework | None = Field(
        default=None,
        description="Test framework to use (auto-detected if None)",
    )
    include_generated: bool = Field(default=True, description="Include AI-generated tests")
    timeout_seconds: int = Field(default=300, ge=30, le=1800)


class GeneratedTestResponse(BaseSchema):
    """Response schema for a generated test."""

    id: str
    file_path: str
    test_file_path: str
    function_name: str | None
    class_name: str | None
    test_type: str
    test_framework: str
    status: str
    content: str
    model_used: str | None
    created_at: datetime


class TestRunResponse(BaseSchema):
    """Response schema for a test run."""

    id: str
    runner: str
    status: str
    started_at: str | None
    finished_at: str | None
    duration_seconds: float | None
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    coverage_percentage: float | None
    failure_summary: str | None
    created_at: datetime


class TestResultResponse(BaseSchema):
    """Response schema for an individual test result."""

    id: str
    test_name: str
    test_file: str | None
    status: str
    duration_seconds: float | None
    failure_message: str | None
    root_cause: str | None
    suggested_fix: str | None
    confidence_score: float | None


class DiscoveredTest(BaseSchema):
    """A single discovered test file."""

    file_path: str
    framework: str
    test_count: int
    test_names: list[str]
    covers_modules: list[str]


class TestDiscoverResponse(BaseSchema):
    """Response from test discovery."""

    total_test_files: int
    total_tests: int
    frameworks_detected: list[str]
    test_files: list[DiscoveredTest]
    uncovered_modules: list[str]
    coverage_gaps: list[str]
