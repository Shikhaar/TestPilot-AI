"""TestPilot AI — EvalOps Telemetry API Endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import APIResponse
from app.services.evalops_collector import EvalOpsMetricsSummary, get_evalops_collector

router = APIRouter()


@router.get("/metrics", response_model=APIResponse[EvalOpsMetricsSummary])
async def get_evalops_metrics() -> APIResponse[EvalOpsMetricsSummary]:
    """Retrieve 4-Category EvalOps quality benchmarks and Last 7 PRs time-series trends."""
    collector = get_evalops_collector()
    metrics = collector.get_latest_metrics()
    return APIResponse(data=metrics)
