"""Pydantic schemas for application checklist endpoints."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    """A single item within an application checklist."""

    id: str | None = None
    description: str
    status: Literal["pending", "in_progress", "completed"] = "pending"
    category: str = "general"
    priority: Literal["high", "medium", "low"] = "medium"


class ChecklistResponse(BaseModel):
    """Response body for an application checklist."""

    id: str
    user_id: str
    program_id: str | None = None
    items: list[ChecklistItem]
    overall_status: Literal["not_started", "in_progress", "completed"] = "not_started"
    completion_percentage: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ChecklistItemUpdate(BaseModel):
    """Request body for updating a single checklist item."""

    status: Literal["pending", "in_progress", "completed"]


class ChecklistCreateRequest(BaseModel):
    """Request body for creating a checklist.

    If ``items`` is empty, the service fills standard document items (CV, transcripts, LOR, SOP, …)
    plus optional program-specific rows from ``program_requirements`` text and ``target_program`` hints.
    """

    user_id: str
    program_id: str | None = None
    items: list[ChecklistItem] = Field(
        default_factory=list,
        description="Explicit rows; leave empty to auto-generate from templates + requirements",
    )
    program_requirements: str | None = Field(
        default=None,
        description="Free-text program checklist (portal copy); used to add GRE, TOEFL, portfolio, etc.",
    )
    target_program: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional flags e.g. requires_gre, requires_gmat, requires_english_test",
    )
