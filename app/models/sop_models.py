"""Pydantic schemas for SOP generation endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class SOPGenerateRequest(BaseModel):
    """Request body for SOP generation."""

    user_id: str
    program_id: str | None = None
    user_profile: dict[str, Any] = Field(default_factory=dict)
    target_program: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    match_attribution: dict[str, Any] = Field(
        default_factory=dict,
        description="Eligibility/match scoring payload; stored as snapshot and injected into prompts",
    )
    parent_sop_id: str | None = Field(default=None, description="Previous SOP version for refinement")
    refinement_instructions: str | None = Field(default=None, description="Instructions for iterative refinement")

    @model_validator(mode="after")
    def require_program_context(self) -> "SOPGenerateRequest":
        """Ensure generation is anchored to a specific program (id or descriptive target_program)."""
        if (self.program_id or "").strip():
            return self
        tp = self.target_program or {}
        keys = (
            "program_name",
            "name",
            "university_name",
            "university",
            "program_title",
            "field_of_study",
        )
        if any(str(tp.get(k) or "").strip() for k in keys):
            return self
        raise ValueError(
            "Provide program_id or target_program with at least one non-empty field among: "
            "program_name, name, university_name, university, program_title, field_of_study"
        )


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
    match_attribution_snapshot: dict[str, Any] | None = None
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
