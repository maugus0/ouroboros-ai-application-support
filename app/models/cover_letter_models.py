"""Pydantic schemas for cover letter generation endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CoverLetterGenerateRequest(BaseModel):
    """Request body for cover letter generation."""

    user_id: str
    target_type: Literal["program", "scholarship", "professor", "other"] = "program"
    target_id: str | None = None
    user_profile: dict[str, Any] = Field(default_factory=dict)
    target_details: dict[str, Any] = Field(default_factory=dict)
    parent_letter_id: str | None = Field(default=None, description="Previous version for refinement")
    refinement_instructions: str | None = None


class CoverLetterResponse(BaseModel):
    """Response body for a generated cover letter."""

    id: str
    user_id: str
    target_type: str
    target_id: str | None = None
    version: int = 1
    content: str
    word_count: int
    llm_model_used: str | None = None
    llm_fallback_used: bool = False
    total_processing_time_ms: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
