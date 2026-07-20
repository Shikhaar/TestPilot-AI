"""TestPilot AI — Review Agent.

Synthesizes all agent outputs into a structured, actionable GitHub PR review.
Incorporates risk scoring, failure analysis, coverage deltas, and historical
bug patterns to produce a review like a senior engineer would write.
"""

from __future__ import annotations

import time
from typing import Any

import instructor
import litellm
from pydantic import BaseModel, Field

from app.agents.state import AgentState, PRReview, RiskScore
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class PRReviewOutput(BaseModel):
    """Structured PR review from LLM."""

    risk_level: str = Field(description="Overall risk: low|medium|high|critical")
    risk_score: float = Field(description="Numeric risk score 0.0-10.0", ge=0.0, le=10.0)
    summary: str = Field(description="2-3 sentence executive summary")
    risk_factors: list[dict[str, str]] = Field(description="List of risk factors with severity")
    action_items: list[str] = Field(description="Ordered list of recommended actions")
    historical_warnings: list[str] = Field(
        description="Warnings from historical bug patterns", default_factory=list
    )
    markdown_review: str = Field(description="Complete Markdown-formatted review body for GitHub")


def review_agent_node(state: AgentState) -> dict[str, Any]:
    """LangGraph node: generate the final AI PR review.

    Args:
        state: Current AgentState with all prior agent outputs.

    Returns:
        Partial state with risk_score and review.
    """
    start_time = time.monotonic()
    logger.info("Review agent started", pr_id=state.get("pr_id"))

    try:
        review_output = _generate_review(state)

        risk_score = RiskScore(
            level=review_output.risk_level,
            score=review_output.risk_score,
            factors=[f["factor"] for f in review_output.risk_factors],
            historical_context="\n".join(review_output.historical_warnings) or None,
        )

        review = PRReview(
            risk_level=review_output.risk_level,
            risk_score=review_output.risk_score,
            summary=review_output.summary,
            risk_factors=review_output.risk_factors,
            action_items=review_output.action_items,
            historical_warnings=review_output.historical_warnings,
            full_review_body=review_output.markdown_review,
        )

        duration = time.monotonic() - start_time
        logger.info(
            "Review agent completed",
            risk_level=review_output.risk_level,
            risk_score=review_output.risk_score,
            duration_ms=int(duration * 1000),
        )

        completed = list(state.get("completed_agents", []))
        completed.append("review_agent")

        return {
            "risk_score": risk_score,
            "review": review,
            "completed_agents": completed,
            "current_agent": "review_agent",
        }

    except Exception as e:
        logger.exception("Review agent failed", error=str(e))
        errors = list(state.get("errors", []))
        errors.append(f"review_agent: {e}")
        return {
            "errors": errors,
            "risk_score": RiskScore(
                level="unknown", score=0.0, factors=[], historical_context=None
            ),
            "review": PRReview(
                risk_level="unknown",
                risk_score=0.0,
                summary="Review generation failed.",
                risk_factors=[],
                action_items=[],
                historical_warnings=[],
                full_review_body="⚠️ TestPilot AI review generation encountered an error.",
            ),
        }


def _generate_review(state: AgentState) -> PRReviewOutput:
    """Generate the PR review using LiteLLM or rule-based fallback."""
    try:
        client = instructor.from_litellm(litellm.completion)
        return _llm_review(client, state)
    except Exception:
        return _rule_based_review(state)


def _llm_review(client: Any, state: AgentState) -> PRReviewOutput:
    """Generate review using LLM with structured output."""
    # Compile all context for the review
    changed_files = state.get("changed_files", [])
    affected_modules = state.get("affected_modules", [])
    affected_apis = state.get("affected_apis", [])
    exec_results = state.get("execution_results", {})
    failure_analyses = state.get("failure_analyses", [])
    generated_tests = state.get("generated_tests", [])
    coverage_gaps = state.get("coverage_gaps", [])

    failures_summary = (
        "\n".join([f"- {fa['test_name']}: {fa['root_cause']}" for fa in failure_analyses[:5]])
        or "No test failures."
    )

    prompt = f"""You are a senior software engineer reviewing a Pull Request.
Write a comprehensive, actionable code review based on the analysis below.

## PR Analysis Results

### Changed Files ({len(changed_files)} files)
{chr(10).join([f"- {f['path']} (+{f['additions']}/-{f['deletions']})" for f in changed_files[:20]])}

### Affected Modules ({len(affected_modules)} modules)
{chr(10).join(affected_modules[:10])}

### Affected APIs
{chr(10).join(affected_apis[:10]) or "None detected"}

### Test Results
- Total: {exec_results.get("total", "N/A")}
- Passed: {exec_results.get("passed", "N/A")}
- Failed: {exec_results.get("failed", "N/A")}
- Coverage: {exec_results.get("coverage_percentage", "N/A")}%

### Test Failures
{failures_summary}

### Generated Tests
{len(generated_tests)} new tests generated for uncovered code.

### Coverage Gaps
{chr(10).join(coverage_gaps[:5]) or "None identified"}

## Your Task
Produce a thorough, constructive PR review. Be specific about risks.
Format the markdown_review as a GitHub PR comment with sections:
🔍 Overview, ⚠️ Risk Assessment, 🧪 Test Coverage, 🔥 Failures Found,
✅ Generated Tests, 📋 Action Items.
"""

    result, _ = client.chat.completions.create_with_completion(
        model=settings.litellm_default_model,
        messages=[{"role": "user", "content": prompt}],
        response_model=PRReviewOutput,
        max_tokens=2048,
        temperature=0.1,
        api_key=settings.gemini_api_key or settings.openai_api_key or None,
    )
    return result


def _rule_based_review(state: AgentState) -> PRReviewOutput:
    """Generate a review using rule-based heuristics when LLM is unavailable."""
    changed_files = state.get("changed_files", [])
    exec_results = state.get("execution_results", {})
    state.get("failure_analyses", [])
    affected_modules = state.get("affected_modules", [])

    failed = exec_results.get("failed", 0)
    total = exec_results.get("total", 0)
    coverage = exec_results.get("coverage_percentage")

    # Calculate risk score
    risk_score = 0.0
    risk_factors = []

    if failed > 0:
        risk_score += min(failed * 1.5, 5.0)
        risk_factors.append({"factor": f"{failed} test(s) failing", "severity": "high"})

    if len(changed_files) > 20:
        risk_score += 2.0
        risk_factors.append({"factor": "Large PR with many changed files", "severity": "medium"})

    if coverage is not None and coverage < settings.coverage_threshold:
        risk_score += 1.5
        risk_factors.append(
            {"factor": f"Coverage below threshold ({coverage:.1f}%)", "severity": "medium"}
        )

    if any("auth" in m.lower() or "payment" in m.lower() for m in affected_modules):
        risk_score += 2.0
        risk_factors.append({"factor": "Auth/payment modules affected", "severity": "high"})

    risk_score = min(risk_score, 10.0)

    if risk_score >= 7.0:
        risk_level = "critical"
    elif risk_score >= 5.0:
        risk_level = "high"
    elif risk_score >= 2.5:
        risk_level = "medium"
    else:
        risk_level = "low"

    action_items = []
    if failed > 0:
        action_items.append(f"Fix {failed} failing test(s) before merging")
    if coverage is not None and coverage < settings.coverage_threshold:
        action_items.append(f"Improve test coverage to at least {settings.coverage_threshold}%")

    markdown_review = _build_markdown_review(
        state, risk_level, risk_score, risk_factors, action_items
    )

    return PRReviewOutput(
        risk_level=risk_level,
        risk_score=round(risk_score, 1),
        summary=f"PR changes {len(changed_files)} files affecting {len(affected_modules)} modules. "
        f"Risk level: {risk_level.upper()}. "
        f"Tests: {exec_results.get('passed', 0)}/{total} passing.",
        risk_factors=risk_factors,
        action_items=action_items,
        historical_warnings=[],
        markdown_review=markdown_review,
    )


def _build_markdown_review(
    state: AgentState,
    risk_level: str,
    risk_score: float,
    risk_factors: list[dict[str, str]],
    action_items: list[str],
) -> str:
    """Build a formatted Markdown review body."""
    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴", "critical": "💀"}.get(risk_level, "⚪")
    exec_results = state.get("execution_results", {})
    changed_files = state.get("changed_files", [])

    lines = [
        "# 🤖 TestPilot AI Analysis",
        "",
        f"## {risk_emoji} Risk Assessment: `{risk_level.upper()}` ({risk_score:.1f}/10.0)",
        "",
        "### Changed Files",
        *[f"- `{f['path']}` (+{f['additions']}/-{f['deletions']})" for f in changed_files[:15]],
        "",
        "### Risk Factors",
        *[f"- **{rf['severity'].upper()}**: {rf['factor']}" for rf in risk_factors],
        "",
        "### Test Results",
        f"- ✅ Passed: {exec_results.get('passed', 'N/A')}",
        f"- ❌ Failed: {exec_results.get('failed', 'N/A')}",
        f"- ⏭️ Skipped: {exec_results.get('skipped', 'N/A')}",
        f"- 📊 Coverage: {exec_results.get('coverage_percentage', 'N/A')}%",
        "",
    ]

    if action_items:
        lines += ["### 📋 Action Items", *[f"- [ ] {item}" for item in action_items], ""]

    lines += ["---", "*Generated by [TestPilot AI](https://github.com/testpilot-ai)*"]

    return "\n".join(lines)
