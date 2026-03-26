"""Tests for deadline service with mocked repository."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.models.deadline_models import DeadlineCreateRequest, DeadlineUpdateRequest
from app.services.deadline_service import DeadlineService


@pytest.mark.asyncio
async def test_create_deadline_allow_db_failure(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)
    svc = DeadlineService(repo=AsyncMock())
    req = DeadlineCreateRequest(
        user_id="u1",
        deadline_date=date(2026, 1, 15),
        item_description="Submit application",
    )
    res = await svc.create(req)
    assert res.user_id == "u1"
    assert res.item_description == "Submit application"


@pytest.mark.asyncio
async def test_list_for_user_empty_when_allow_db_failure(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)
    svc = DeadlineService(repo=AsyncMock())
    rows = await svc.list_for_user("u1")
    assert rows == []


@pytest.mark.asyncio
async def test_update_delegates_to_repo(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", False)
    repo = MagicMock()
    row = {
        "id": "d1",
        "user_id": "u1",
        "checklist_id": None,
        "deadline_date": date(2026, 2, 1),
        "deadline_time": None,
        "item_description": "x",
        "item_category": "application",
        "priority": "medium",
        "status": "pending",
        "reminder_sent": False,
        "reminder_sent_at": None,
        "created_at": None,
        "updated_at": None,
    }
    row_after = {**row, "priority": "high", "status": "completed"}
    repo.get_by_id = AsyncMock(side_effect=[row, row_after])
    repo.update = AsyncMock(return_value=1)

    svc = DeadlineService(repo=repo)
    res = await svc.update("d1", DeadlineUpdateRequest(priority="high", status="completed"))
    assert res.priority == "high"
    assert res.status == "completed"
    repo.update.assert_awaited_once()
