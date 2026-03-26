"""Pydantic schemas for validating LLM output structure."""

from pydantic import BaseModel, Field


class SOPOutlineOutput(BaseModel):
    """Expected output from the SOP outline step."""

    introduction_theme: str
    body_points: list[str]
    conclusion_theme: str
    suggested_tone: str = "professional"


class SOPQualityReviewOutput(BaseModel):
    """Expected output from the SOP quality review step."""

    revised_content: str
    quality_score: float = Field(..., ge=0.0, le=1.0)
    feedback: list[str] = Field(default_factory=list)
    word_count: int = 0


class CoverLetterOutput(BaseModel):
    """Expected output from cover letter generation."""

    content: str
    word_count: int = 0
    tone_assessment: str = ""


class CVImprovementOutput(BaseModel):
    """Expected output from CV improvement analysis."""

    suggestions: list[str]
    priority_areas: list[str]
    overall_assessment: str
