"""TestPilot AI — EvalOps Telemetry API Endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DBSession
from app.schemas.common import APIResponse
from app.services.evalops_collector import EvalOpsMetricsSummary, get_evalops_collector

router = APIRouter()


@router.get("/metrics", response_model=APIResponse[EvalOpsMetricsSummary])
async def get_evalops_metrics(db: DBSession) -> APIResponse[EvalOpsMetricsSummary]:
    """Retrieve 4-Category EvalOps quality benchmarks and Last 7 PRs time-series trends."""
    collector = get_evalops_collector()
    metrics = await collector.get_latest_metrics(db=db)
    return APIResponse(data=metrics)
