"""Tests for checklist completion logic."""

from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.services.checklist_service import ChecklistService
from app.utils.exceptions import ValidationError


def test_compute_status_empty_items():
    overall, pct = ChecklistService.compute_status([])
    assert overall == "not_started"
    assert pct == 0.0


def test_compute_status_all_completed():
    items = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "completed"},
    ]
    overall, pct = ChecklistService.compute_status(items)
    assert overall == "completed"
    assert pct == 100.0


def test_compute_status_in_progress():
    items = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "pending"},
    ]
    overall, pct = ChecklistService.compute_status(items)
    assert overall == "in_progress"
    assert pct == 50.0


def test_compute_status_explicit_in_progress():
    items = [
        {"id": "1", "status": "in_progress"},
        {"id": "2", "status": "pending"},
    ]
    overall, pct = ChecklistService.compute_status(items)
    assert overall == "in_progress"
    assert pct == 0.0


@pytest.mark.asyncio
async def test_update_item_invalid_json_raises(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", False)
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value={"id": "c1", "user_id": "u1", "items": "{not-json", "program_id": None})
    svc = ChecklistService(repo=repo)
    with pytest.raises(ValidationError, match="invalid JSON"):
        await svc.update_item("c1", "i1", "completed")


@pytest.mark.asyncio
async def test_update_item_non_array_json_raises(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", False)
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value={"id": "c1", "user_id": "u1", "items": '{"a":1}', "program_id": None})
    svc = ChecklistService(repo=repo)
    with pytest.raises(ValidationError, match="JSON array"):
        await svc.update_item("c1", "i1", "completed")
