"""Tests for prompt template loading and context injection."""

import json

import pytest

from app.utils.prompt_utils import build_prompt_json, build_prompt_text, load_prompt_template, merge_runtime_context


def test_load_sop_outline_template():
    template = load_prompt_template("sop_outline_v1.json")
    assert "prompt_template" in template
    assert "base" in template["prompt_template"]


def test_load_nonexistent_template():
    with pytest.raises(FileNotFoundError):
        load_prompt_template("nonexistent.json")


def test_merge_runtime_context_without_context():
    template = load_prompt_template("sop_outline_v1.json")
    result = merge_runtime_context(template)
    assert "runtime_context" not in result


def test_merge_runtime_context_with_context():
    template = load_prompt_template("sop_outline_v1.json")
    result = merge_runtime_context(template, {"user_name": "Alice"})
    assert "runtime_context" in result
    assert result["runtime_context"]["user_name"] == "Alice"


def test_build_prompt_json():
    result = build_prompt_json("sop_outline_v1.json", {"field": "CS"})
    parsed = json.loads(result)
    assert "agent_identity" in parsed
    assert parsed["runtime_context"]["field"] == "CS"


def test_build_prompt_text():
    result = build_prompt_text("sop_outline_v1.json", {"field": "CS"})
    assert "AGENT IDENTITY" in result
    assert isinstance(result, str)
