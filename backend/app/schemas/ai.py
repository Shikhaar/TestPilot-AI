"""TestPilot AI — AI / LLM Pydantic Schemas."""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseSchema


class ChatMessage(BaseSchema):
    """A single message in a chat conversation."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseSchema):
    """Request to chat with the codebase."""

    repository_id: str
    messages: list[ChatMessage]
    context_files: list[str] = Field(
        default_factory=list,
        description="Specific files to include in context",
    )
    max_tokens: int = Field(default=2048, le=8192)


class ChatResponse(BaseSchema):
    """Response from codebase chat."""

    message: ChatMessage
    sources: list[str] = Field(default_factory=list, description="Source file paths referenced")
    tokens_used: int


class CodeSearchRequest(BaseSchema):
    """Semantic code search request."""

    repository_id: str
    query: str = Field(..., min_length=3, description="Natural language search query")
    limit: int = Field(default=10, ge=1, le=50)
    search_type: str = Field(
        default="hybrid",
        description="Search strategy: 'semantic' | 'structural' | 'hybrid'",
    )
    filters: dict[str, str] = Field(
        default_factory=dict,
        description="Optional filters: language, file_type, etc.",
    )


class CodeSearchResult(BaseSchema):
    """A single code search result."""

    file_path: str
    language: str
    snippet: str
    score: float
    function_name: str | None
    class_name: str | None
    line_start: int | None
    line_end: int | None


class CodeSearchResponse(BaseSchema):
    """Response from code search."""

    results: list[CodeSearchResult]
    total: int
    query: str
    search_type: str


class ImpactAnalysisRequest(BaseSchema):
    """Request for manual impact analysis."""

    repository_id: str
    changed_files: list[str]
    depth: int = Field(default=3, ge=1, le=10, description="Graph traversal depth")


class RiskScoreRequest(BaseSchema):
    """Request for PR risk scoring."""

    pr_id: str
    include_historical: bool = Field(
        default=True,
        description="Include historical bug pattern analysis",
    )
