"""TestPilot AI — Failure Analysis Agent.

When tests fail, this agent uses LiteLLM to perform AI-powered root cause
analysis. Instead of just repeating the stack trace, it:
1. Identifies the root cause of the failure
2. Traces it to the specific changed code
3. Suggests a concrete fix
4. Assigns a confidence score
"""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.agents.state import AgentState, FailureAnalysis
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class FailureAnalysisResult(BaseModel):
    """Structured failure analysis from LLM."""

    root_cause: str = Field(description="The underlying root cause of the failure")
    affected_code_path: str | None = Field(description="The file/function that caused the failure")
    suggested_fix: str = Field(description="Concrete code suggestion to fix the failure")
    is_pr_regression: bool = Field(
        description="Whether this failure was introduced by the PR changes"
    )
    confidence: float = Field(description="Confidence score 0.0-1.0", ge=0.0, le=1.0)
    explanation: str = Field(description="Human-readable explanation of the analysis")


def failure_analysis_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: analyze test failures with AI root cause analysis.

    Args:
        state: Current AgentState with execution_results.

    Returns:
        Partial state with failure_analyses.
    """
    start_time = time.monotonic()
    logger.info("Failure analysis agent started", pr_id=state.get("pr_id"))

    try:
        execution_results = state.get("execution_results", {})
        failed_tests = execution_results.get("failed_tests", [])

        if not failed_tests:
            completed = list(state.get("completed_agents", []))
            completed.append("failure_analysis_agent")
            return {"failure_analyses": [], "completed_agents": completed}

        analyses = []
        for failed_test in failed_tests[:10]:  # Analyze top 10 failures
            analysis = _analyze_failure(failed_test, state)
            if analysis:
                analyses.append(analysis)

        duration = time.monotonic() - start_time
        logger.info(
            "Failure analysis agent completed",
            analyzed=len(analyses),
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("failure_analysis_agent")

        return {
            "failure_analyses": analyses,
            "completed_agents": completed,
            "current_agent": "failure_analysis_agent",
        }

    except Exception as e:
        logger.exception("Failure analysis agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"failure_analysis_agent: {e}")
        return {"errors": errors, "failure_analyses": []}


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type(Exception),
    reraise=False,
)
def _analyze_failure(
    failed_test: dict[str, Any],
    state: AgentState,
) -> FailureAnalysis | None:
    """Use LiteLLM to analyze a single test failure."""
    try:
        import instructor
        import litellm

        client = instructor.from_litellm(litellm.completion)
    except ImportError:
        return _mock_analysis(failed_test)

    changed_files = "\n".join([f"- {f['path']}" for f in state.get("changed_files", [])[:10]])
    changed_nodes = "\n".join(
        [
            f"- {n['type']}: {n['name']} in {n['file_path']}"
            for n in state.get("changed_nodes", [])[:10]
        ]
    )

    prompt = f"""You are an expert software engineer performing test failure root cause analysis.

## Failed Test
Test Name: {failed_test.get("name", "unknown")}
Failure Message: {failed_test.get("message", "")[:2000]}

## Changed Code in This PR
Files Changed:
{changed_files}

Functions/Classes Modified:
{changed_nodes}

## Task
Analyze this test failure and determine:
1. The root cause (not just the error message — what ACTUALLY went wrong)
2. Whether this failure was introduced by the PR changes above
3. A specific, actionable fix suggestion
4. Your confidence in this analysis (0.0 = uncertain, 1.0 = certain)

Focus on being precise and practical. If this failure is a pre-existing issue
unrelated to the PR changes, say so clearly.
"""

    try:
        result, _ = client.chat.completions.create_with_completion(
            model=settings.litellm_default_model,
            messages=[{"role": "user", "content": prompt}],
            response_model=FailureAnalysisResult,
            max_tokens=1024,
            temperature=0.0,
            api_key=settings.gemini_api_key or settings.openai_api_key or None,
        )

        return FailureAnalysis(
            test_name=failed_test.get("name", "unknown"),
            failure_message=failed_test.get("message", ""),
            root_cause=result.root_cause,
            affected_code_path=result.affected_code_path,
            suggested_fix=result.suggested_fix,
            confidence=result.confidence,
        )

    except Exception as e:
        logger.warning("LLM failure analysis failed", test=failed_test.get("name"), error=str(e))
        return _mock_analysis(failed_test)


def _mock_analysis(failed_test: dict[str, Any]) -> FailureAnalysis:
    """Return a placeholder analysis when LLM is unavailable."""
    return FailureAnalysis(
        test_name=failed_test.get("name", "unknown"),
        failure_message=failed_test.get("message", ""),
        root_cause="Manual analysis required — AI analysis unavailable.",
        affected_code_path=None,
        suggested_fix="Review the stack trace and compare against recent changes.",
        confidence=0.0,
    )
