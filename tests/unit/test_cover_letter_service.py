"""Tests for cover letter generation service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.models.cover_letter_models import CoverLetterGenerateRequest
from app.services.cover_letter_service import CoverLetterService


@pytest.mark.asyncio
async def test_generate_parent_skips_repo_lookup_when_allow_db_failure(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_DATA", False)
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")

    llm = MagicMock()
    llm.generate = AsyncMock(
        return_value={
            "content": {"content": "hello world", "word_count": 2, "tone_assessment": "formal"},
            "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
        }
    )
    repo = AsyncMock()
    svc = CoverLetterService(llm=llm, repo=repo)
    req = CoverLetterGenerateRequest(
        user_id="user-1",
        user_profile={"name": "A"},
        target_details={"org": "X"},
        parent_letter_id="prev-1",
    )
    res = await svc.generate(req)
    assert res.version == 1
    repo.get_by_id.assert_not_called()
