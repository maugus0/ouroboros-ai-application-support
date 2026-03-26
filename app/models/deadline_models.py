"""Pydantic schemas for deadline tracking endpoints."""

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field


class DeadlineCreateRequest(BaseModel):
    """Request body for creating a deadline entry."""

    user_id: str
    checklist_id: str | None = None
    deadline_date: date
    deadline_time: time | None = None
    item_description: str = Field(..., max_length=500)
    item_category: Literal["application", "document", "test", "interview", "other"] = "application"
    priority: Literal["high", "medium", "low"] = "medium"


class DeadlineUpdateRequest(BaseModel):
    """Request body for updating a deadline entry."""

    deadline_date: date | None = None
    deadline_time: time | None = None
    item_description: str | None = Field(default=None, max_length=500)
    item_category: Literal["application", "document", "test", "interview", "other"] | None = None
    priority: Literal["high", "medium", "low"] | None = None
    status: Literal["pending", "completed", "missed"] | None = None


class DeadlineResponse(BaseModel):
    """Response body for a deadline entry."""

    id: str
    user_id: str
    checklist_id: str | None = None
    deadline_date: date
    deadline_time: time | None = None
    item_description: str
    item_category: str = "application"
    priority: str = "medium"
    status: str = "pending"
    reminder_sent: bool = False
    reminder_sent_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
