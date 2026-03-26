"""Pydantic schemas for SOP generation endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SOPGenerateRequest(BaseModel):
    """Request body for SOP generation."""

    user_id: str
    program_id: str | None = None
    user_profile: dict[str, Any] = Field(default_factory=dict)
    target_program: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    parent_sop_id: str | None = Field(default=None, description="Previous SOP version for refinement")
    refinement_instructions: str | None = Field(default=None, description="Instructions for iterative refinement")


class SOPResponse(BaseModel):
    """Response body for a generated SOP."""

    id: str
    user_id: str
    program_id: str | None = None
    version: int = 1
    content: str
    word_count: int
    quality_score: float | None = None
    quality_feedback: list[str] | None = None
    llm_model_used: str | None = None
    llm_fallback_used: bool = False
    total_processing_time_ms: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SOPVersionListResponse(BaseModel):
    """Response listing all versions of an SOP."""

    sop_id: str
    versions: list[SOPResponse]
    total_versions: int
