"""State management for multi-step LLM pipelines."""

from typing import Any

from pydantic import BaseModel, Field


class SOPPipelineState(BaseModel):
    """State passed through SOP generation pipeline."""

    # Input data
    user_profile: dict[str, Any] = Field(default_factory=dict)
    target_program: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    retrieved_references: list[dict[str, Any]] = Field(default_factory=list)

    # Pipeline outputs (accumulated across steps)
    outline: str | None = None
    expanded_content: str | None = None
    final_content: str | None = None

    # Quality metadata
    quality_score: float | None = None
    quality_feedback: list[str] = Field(default_factory=list)

    # Pipeline metadata
    current_step: str = "init"
    steps_completed: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    # LLM call tracking
    llm_calls: list[dict[str, Any]] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost_usd: float = 0.0
