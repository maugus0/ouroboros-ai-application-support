"""Pydantic schemas for application checklist endpoints."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChecklistItem(BaseModel):
    """A single item within an application checklist."""

    id: str
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
