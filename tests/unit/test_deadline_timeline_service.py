"""DeadlineService timeline + sync with in-memory repository."""

from datetime import date, timedelta

import pytest

from app.config import settings
from app.models.deadline_models import DeadlineCreateRequest
from app.services.deadline_service import DeadlineService
from tests.fake_repos import FakeDeadlineRepository


@pytest.mark.asyncio
async def test_list_timeline_sorted_and_marks_past(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", False)
    repo = FakeDeadlineRepository()
    svc = DeadlineService(repo=repo)
    ref = date(2026, 6, 15)
    await svc.create(
        DeadlineCreateRequest(
            user_id="u1",
            deadline_date=ref + timedelta(days=60),
            item_description="Far future",
        )
    )
    await svc.create(
        DeadlineCreateRequest(
            user_id="u1",
            deadline_date=ref - timedelta(days=2),
            item_description="Already passed",
        )
    )
    items = await svc.list_timeline_for_user("u1", reference_date=ref, approaching_days=30)
    assert [x.item_description for x in items] == ["Already passed", "Far future"]
    past = next(x for x in items if x.item_description == "Already passed")
    future = next(x for x in items if x.item_description == "Far future")
    assert past.timeline_status == "passed"
    assert past.is_past is True
    assert future.timeline_status == "upcoming"
    assert future.is_highlighted is False


@pytest.mark.asyncio
async def test_sync_skips_duplicates(monkeypatch):
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", False)
    repo = FakeDeadlineRepository()
    svc = DeadlineService(repo=repo)
    programs = [{"program_id": "p1", "program_name": "Test", "application_deadline": "2026-08-01"}]
    first = await svc.sync_from_sources("u1", programs, [])
    assert first.created_count == 1
    assert first.skipped_duplicates == 0
    second = await svc.sync_from_sources("u1", programs, [])
    assert second.created_count == 0
    assert second.skipped_duplicates == 1
