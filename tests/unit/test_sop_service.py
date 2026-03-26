"""Tests for SOP service orchestration (mocked LLM)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.models.sop_models import SOPGenerateRequest
from app.services.sop_service import SOPService


@pytest.mark.asyncio
async def test_generate_mock_data_path(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_DATA", True)
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)

    llm = AsyncMock()
    svc = SOPService(
        llm=llm,
        sop_repo=AsyncMock(),
        retrieval=AsyncMock(),
    )
    req = SOPGenerateRequest(user_id="user-1", program_id="prog-1")
    res = await svc.generate(req)
    assert res.user_id == "user-1"
    assert res.program_id == "prog-1"
    assert "mock" in res.content.lower()
    llm.generate.assert_not_called()


@pytest.mark.asyncio
async def test_generate_calls_llm_when_not_mock(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_DATA", False)
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")

    llm = MagicMock()
    llm.generate = AsyncMock(
        side_effect=[
            {
                "content": {
                    "introduction_theme": "t",
                    "body_points": ["a", "b"],
                    "conclusion_theme": "c",
                    "suggested_tone": "professional",
                },
                "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
            },
            {
                "content": " ".join(["word"] * 600),
                "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
            },
            {
                "content": {
                    "revised_content": " ".join(["word"] * 620),
                    "quality_score": 0.82,
                    "feedback": ["ok"],
                    "word_count": 620,
                },
                "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
            },
        ]
    )
    retrieval = MagicMock()
    retrieval.fetch_references = AsyncMock(return_value=[])

    svc = SOPService(llm=llm, sop_repo=AsyncMock(), retrieval=retrieval)
    req = SOPGenerateRequest(user_id="user-1", user_profile={"name": "A"}, target_program={"field_of_study": "CS"})
    res = await svc.generate(req)
    assert res.user_id == "user-1"
    assert res.word_count >= 500
    assert llm.generate.await_count == 3


@pytest.mark.asyncio
async def test_generate_parent_skips_repo_lookup_when_allow_db_failure(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_DATA", False)
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")

    llm = MagicMock()
    llm.generate = AsyncMock(
        side_effect=[
            {
                "content": {
                    "introduction_theme": "t",
                    "body_points": ["a", "b"],
                    "conclusion_theme": "c",
                    "suggested_tone": "professional",
                },
                "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
            },
            {
                "content": " ".join(["word"] * 600),
                "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
            },
            {
                "content": {
                    "revised_content": " ".join(["word"] * 620),
                    "quality_score": 0.82,
                    "feedback": ["ok"],
                    "word_count": 620,
                },
                "metadata": {"llm_provider": "openai", "model_name": "gpt-test"},
            },
        ]
    )
    retrieval = MagicMock()
    retrieval.fetch_references = AsyncMock(return_value=[])

    sop_repo = AsyncMock()
    svc = SOPService(llm=llm, sop_repo=sop_repo, retrieval=retrieval)
    req = SOPGenerateRequest(
        user_id="user-1",
        user_profile={"name": "A"},
        target_program={"field_of_study": "CS"},
        parent_sop_id="parent-1",
    )
    res = await svc.generate(req)
    assert res.version == 1
    sop_repo.get_by_id.assert_not_called()
