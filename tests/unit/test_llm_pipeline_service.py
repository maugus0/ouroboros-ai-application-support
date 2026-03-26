"""Tests for LLM pipeline service provider selection."""

from unittest.mock import patch

import pytest

from app.config import settings
from app.services.llm_pipeline_service import LLMPipelineService
from app.utils.exceptions import LLMGenerationError


@pytest.mark.asyncio
async def test_generate_openai_success(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)

    async def fake_openai(*_args, **_kwargs):
        return {
            "content": '{"hello": "world"}',
            "model": "gpt-test",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        }

    with patch("app.services.llm_pipeline_service.call_openai", new=fake_openai):
        svc = LLMPipelineService()
        out = await svc.generate(
            system_prompt="sys",
            user_content="user",
            operation="test_op",
            max_tokens=100,
            response_format="json",
        )
    assert out["content"] == {"hello": "world"}
    assert out["metadata"]["llm_provider"] == "openai"


@pytest.mark.asyncio
async def test_generate_falls_back_to_anthropic(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)

    async def fail_openai(*_args, **_kwargs):
        raise RuntimeError("openai down")

    async def ok_anthropic(*_args, **_kwargs):
        return {
            "content": '{"a": 1}',
            "model": "claude-test",
            "input_tokens": 3,
            "output_tokens": 4,
        }

    with (
        patch("app.services.llm_pipeline_service.call_openai", new=fail_openai),
        patch("app.services.llm_pipeline_service.call_anthropic", new=ok_anthropic),
    ):
        svc = LLMPipelineService()
        out = await svc.generate(
            system_prompt="sys",
            user_content="user",
            operation="test_op",
            max_tokens=100,
            response_format="json",
        )
    assert out["content"] == {"a": 1}
    assert out["metadata"]["llm_provider"] == "anthropic"


@pytest.mark.asyncio
async def test_generate_raises_when_no_keys(monkeypatch):
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(settings, "ALLOW_DB_FAILURE", True)

    svc = LLMPipelineService()
    with pytest.raises(LLMGenerationError):
        await svc.generate(
            system_prompt="s",
            user_content="u",
            operation="op",
            max_tokens=10,
        )
