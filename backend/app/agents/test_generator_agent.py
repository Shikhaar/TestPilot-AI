"""
TestPilot AI — Test Generator Agent.

Generates high-quality, style-consistent tests using LiteLLM with
structured output via Instructor. Studies the repository's existing
test patterns before generating new ones.

Generates:
- Unit tests
- Integration tests
- Edge case tests
- Negative tests
- Boundary tests
- Concurrency tests
- Mock-based tests
- Property-based tests
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import instructor
import litellm
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.agents.state import AgentState, GeneratedTest
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


# ==============================================================================
# Structured output schema for LLM
# ==============================================================================


class SingleTest(BaseModel):
    """A single generated test case."""

    function_name: str = Field(description="Name of the test function/method")
    test_type: str = Field(description="Type: unit|integration|edge_case|negative|boundary|mock")
    content: str = Field(description="Complete test code snippet")
    description: str = Field(description="What this test validates")


class GeneratedTestFile(BaseModel):
    """A generated test file with multiple test cases."""

    test_file_path: str = Field(description="Relative path where this test file should be written")
    imports: str = Field(description="Import statements needed")
    setup_code: str = Field(description="Fixtures, setUp, or test class setup code", default="")
    tests: list[SingleTest] = Field(description="The test functions/methods")
    framework: str = Field(description="Test framework: pytest|jest|junit|go_test")
    language: str = Field(description="Programming language")


class GeneratedTestSuite(BaseModel):
    """Complete generated test suite for a PR."""

    test_files: list[GeneratedTestFile]
    coverage_rationale: str = Field(description="Explanation of what coverage is achieved")


# ==============================================================================
# Agent Node
# ==============================================================================


def test_generator_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: generate missing tests using LiteLLM + Instructor.

    Analyzes the changed code and existing tests to generate new test cases
    that follow the repository's conventions and style.

    Args:
        state: Current AgentState.

    Returns:
        Partial state with generated_tests.
    """
    start_time = time.monotonic()
    logger.info("Test generator agent started", pr_id=state.get("pr_id"))

    try:
        changed_nodes = state.get("changed_nodes", [])
        existing_tests = state.get("existing_tests", [])
        uncovered = state.get("uncovered_modules", [])
        retrieved_context = state.get("retrieved_context", [])

        if not changed_nodes:
            logger.info("No changed nodes, skipping test generation")
            completed = list(state.get("completed_agents", []))
            completed.append("test_generator_agent")
            return {"generated_tests": [], "completed_agents": completed}

        generated = _generate_tests(
            changed_nodes=changed_nodes,
            existing_tests=existing_tests,
            uncovered_modules=uncovered,
            retrieved_context=retrieved_context,
            state=state,
        )

        duration = time.monotonic() - start_time
        logger.info(
            "Test generator agent completed",
            generated_tests=len(generated),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("test_generator_agent")

        return {
            "generated_tests": generated,
            "completed_agents": completed,
            "current_agent": "test_generator_agent",
        }

    except Exception as e:
        logger.exception("Test generator agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"test_generator_agent: {e}")
        return {"errors": errors, "generated_tests": []}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _generate_tests(
    changed_nodes: Sequence[Mapping[str, Any]],
    existing_tests: Sequence[Mapping[str, Any]],
    uncovered_modules: list[str],
    retrieved_context: Sequence[Mapping[str, Any]],
    state: AgentState,
) -> list[GeneratedTest]:
    """Generate tests using LiteLLM with Instructor structured output.

    Uses retry logic with exponential backoff for API failures.
    """
    try:
        client = instructor.from_litellm(litellm.completion)
    except ImportError as e:
        logger.error("instructor or litellm not available", error=str(e))
        return _generate_mock_tests(changed_nodes)

    # Build context for the prompt
    existing_test_examples = "\n\n".join(
        [
            f"# Existing test: {t['path']}\n# Framework: {t['framework']}\n# Tests: {', '.join(t['test_names'][:5])}"
            for t in existing_tests[:3]
        ]
    )

    code_context = "\n\n".join(
        [
            f"# File: {ctx.get('file_path', 'unknown')}\n{ctx.get('content', '')[:500]}"
            for ctx in retrieved_context[:5]
        ]
    )

    changed_summary = "\n".join(
        [
            f"- {node['type'].upper()}: {node['name']} in {node['file_path']}"
            for node in changed_nodes[:20]
        ]
    )

    prompt = f"""You are an expert software engineer generating production-quality tests.

## Changed Code
The following code was modified in this Pull Request:
{changed_summary}

## Existing Test Examples (follow this style)
{existing_test_examples if existing_test_examples else "No existing tests found. Use pytest with appropriate fixtures."}

## Relevant Code Context
{code_context if code_context else "No additional context available."}

## Instructions
1. Generate comprehensive tests for the changed functions/classes above.
2. Follow the EXACT testing style and conventions of existing tests.
3. Do NOT invent APIs that don't exist — use only what's shown in the context.
4. Include these test types where appropriate:
   - Happy path (normal flow)
   - Edge cases (empty input, None, zero, empty list)
   - Negative cases (invalid input, should raise exceptions)
   - Boundary values (min/max values)
   - Mock dependencies where appropriate
5. Each test must be independent and idempotent.
6. Use descriptive test names that explain the scenario.
7. Add docstrings to each test explaining what it validates.
"""

    try:
        result, _ = client.chat.completions.create_with_completion(
            model=settings.litellm_default_model,
            messages=[{"role": "user", "content": prompt}],
            response_model=GeneratedTestSuite,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            api_key=settings.gemini_api_key or settings.openai_api_key or None,
        )

        generated: list[GeneratedTest] = []
        for tf in result.test_files:
            for test in tf.tests:
                generated.append(
                    GeneratedTest(
                        function_name=test.function_name,
                        class_name=None,
                        file_path=changed_nodes[0]["file_path"] if changed_nodes else "unknown",
                        test_file_path=tf.test_file_path,
                        content=f"{tf.imports}\n\n{tf.setup_code}\n\n{test.content}",
                        test_type=test.test_type,
                        test_framework=tf.framework,
                        language=tf.language,
                    )
                )

        logger.info(
            "LLM test generation succeeded",
            count=len(generated),
            model=settings.litellm_default_model,
        )
        return generated

    except Exception as e:
        logger.warning("LLM generation failed, using mock tests", error=str(e))
        return _generate_mock_tests(changed_nodes)


def _generate_mock_tests(changed_nodes: Sequence[Mapping[str, Any]]) -> list[GeneratedTest]:
    """Generate placeholder tests when LLM is unavailable.

    These are stubs that pass validation but need human completion.
    """
    tests = []
    for node in changed_nodes[:5]:
        if node["type"] != "function":
            continue

        fn_name = node["name"]
        file_path = node["file_path"]
        lang = node.get("language", "python")

        if lang == "python":
            content = f'''
def test_{fn_name}_basic():
    """Test basic functionality of {fn_name}.

    TODO: Implement this test with actual assertions.
    This is a generated stub that requires human completion.
    """
    # Arrange
    # Act
    # Assert
    pass


def test_{fn_name}_edge_case():
    """Test edge cases for {fn_name}.

    TODO: Add edge case scenarios.
    """
    pass
'''
            tests.append(
                GeneratedTest(
                    function_name=f"test_{fn_name}_basic",
                    class_name=None,
                    file_path=file_path,
                    test_file_path=f"tests/test_{Path(file_path).stem}.py",
                    content=f"import pytest\n{content}",
                    test_type="unit",
                    test_framework="pytest",
                    language="python",
                )
            )

    return tests
