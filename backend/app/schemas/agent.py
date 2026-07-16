"""TestPilot AI — Agent Run Pydantic Schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import BaseSchema


class AgentRunResponse(BaseSchema):
    """Response schema for a single agent execution step."""

    id: str
    pull_request_id: str
    agent_name: str
    status: str
    started_at: str | None
    finished_at: str | None
    duration_ms: int | None
    input_data: str | None
    output_data: str | None
    error_message: str | None
    retry_count: int
    llm_calls: int
    total_tokens: int
    created_at: datetime
    updated_at: datetime


class AgentPipelineStatusResponse(BaseSchema):
    """Aggregated status of the multi-agent pipeline for a PR."""

    pull_request_id: str
    current_agent: str | None
    completed_agents: list[str] = Field(default_factory=list)
    status: str
    total_duration_ms: int
    errors: list[str] = Field(default_factory=list)
    runs: list[AgentRunResponse] = Field(default_factory=list)
