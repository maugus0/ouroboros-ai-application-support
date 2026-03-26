"""Pydantic schemas for LLM pipeline metadata."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LLMCallMetadata(BaseModel):
    """Metadata for a single LLM call within the pipeline."""

    operation: str
    llm_provider: Literal["openai", "anthropic"]
    model_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    success: bool = True
    error_message: str | None = None
    retry_count: int = 0


class LLMPipelineResult(BaseModel):
    """Result of a multi-step LLM pipeline execution."""

    content: str
    metadata: LLMCallMetadata


class QualityScore(BaseModel):
    """Quality assessment of generated content."""

    score: float = Field(..., ge=0.0, le=1.0)
    feedback: list[str] = Field(default_factory=list)
    passed_threshold: bool = True


class LLMCallLog(BaseModel):
    """Audit log entry for an LLM call."""

    id: str
    operation: str
    sop_id: str | None = None
    cover_letter_id: str | None = None
    llm_provider: str
    model_name: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_cost_usd: float | None = None
    latency_ms: int | None = None
    success: bool
    error_message: str | None = None
    retry_count: int = 0
    trace_id: str
    created_at: datetime | None = None
