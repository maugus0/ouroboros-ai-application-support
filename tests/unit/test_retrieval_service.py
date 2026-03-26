"""Tests for retrieval service."""

from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.services.retrieval_service import RetrievalService


@pytest.mark.asyncio
async def test_fetch_references_disabled(monkeypatch):
    monkeypatch.setattr(settings, "RETRIEVAL_ENABLED", False)
    repo = AsyncMock()
    svc = RetrievalService(repo=repo)
    rows = await svc.fetch_references(field_of_study="CS")
    assert rows == []
    repo.find_references.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_references_returns_repo_rows(monkeypatch):
    monkeypatch.setattr(settings, "RETRIEVAL_ENABLED", True)
    monkeypatch.setattr(settings, "RETRIEVAL_TOP_K", 2)
    repo = AsyncMock()
    repo.find_references = AsyncMock(return_value=[{"id": "r1", "content": "x"}])
    svc = RetrievalService(repo=repo)
    rows = await svc.fetch_references(field_of_study="Biology")
    assert len(rows) == 1
    assert rows[0]["id"] == "r1"
