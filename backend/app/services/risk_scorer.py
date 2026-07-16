"""
TestPilot AI — Risk Scorer Service.

Evaluates changed files, impact radius, test execution results, and
historical context to compute a PR risk score and category.
"""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings

settings = get_settings()


class RiskScorer:
    """Service to assess change risk level and score."""

    @staticmethod
    def calculate_score(
        changed_files: list[dict[str, Any]],
        impact_radius: int,
        test_failures: int,
        coverage_percentage: float | None,
        affected_modules: list[str],
    ) -> dict[str, Any]:
        """Assess the risk profile of a Pull Request.

        Args:
            changed_files: List of files with additions/deletions.
            impact_radius: Number of downstream affected files.
            test_failures: Number of failing test cases.
            coverage_percentage: Coverage status of target repository.
            affected_modules: List of module paths affected.

        Returns:
            Dictionary containing risk level (low/medium/high/critical) and risk score.
        """
        score = 1.0

        factors = []

        # File count impact
        if len(changed_files) > 15:
            score += 2.0
            factors.append("Large pull request change size")
        elif len(changed_files) > 5:
            score += 1.0
            factors.append("Moderate pull request change size")

        # Code churn additions/deletions
        total_churn = sum(f.get("additions", 0) + f.get("deletions", 0) for f in changed_files)
        if total_churn > 1000:
            score += 1.5
            factors.append("High volume of line churn")

        # Dependency graph impact
        if impact_radius > 10:
            score += 2.5
            factors.append("Widespread downstream module impact")
        elif impact_radius > 3:
            score += 1.0
            factors.append("Moderate downstream module impact")

        # High risk components
        for module in affected_modules:
            if any(k in module.lower() for k in ("auth", "security", "payment", "billing", "db")):
                score += 1.5
                factors.append(f"Modifies high-risk module: {module}")
                break

        # Failing tests
        if test_failures > 0:
            score += min(test_failures * 1.5, 4.0)
            factors.append(f"{test_failures} test suite failure(s) detected")

        # Low coverage
        if coverage_percentage is not None and coverage_percentage < settings.coverage_threshold:
            score += 1.0
            factors.append(f"Repository coverage below threshold ({coverage_percentage:.1f}%)")

        # Cap score
        score = min(round(score, 1), 10.0)

        # Map to level
        if score >= 7.5:
            level = "critical"
        elif score >= 5.0:
            level = "high"
        elif score >= 2.5:
            level = "medium"
        else:
            level = "low"

        return {
            "score": score,
            "level": level,
            "factors": factors,
        }
