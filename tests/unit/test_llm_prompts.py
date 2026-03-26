"""Tests for LLM prompt generation functions."""

import json

import pytest

from app.llm.prompts import (
    get_cover_letter_prompt,
    get_cv_improvement_prompt,
    get_sop_expansion_prompt,
    get_sop_outline_prompt,
    get_sop_quality_review_prompt,
)


def test_sop_outline_prompt_json():
    result = get_sop_outline_prompt(context={"field": "CS"}, fmt="json")
    parsed = json.loads(result)
    assert "agent_identity" in parsed


def test_sop_outline_prompt_text():
    result = get_sop_outline_prompt(context={"field": "CS"}, fmt="text")
    assert "AGENT IDENTITY" in result


def test_sop_expansion_prompt():
    result = get_sop_expansion_prompt(fmt="json")
    parsed = json.loads(result)
    assert "task_instructions" in parsed


def test_sop_quality_review_prompt():
    result = get_sop_quality_review_prompt(fmt="json")
    parsed = json.loads(result)
    assert "quality_criteria" in parsed


def test_cover_letter_prompt():
    result = get_cover_letter_prompt(context={"target": "MIT"}, fmt="json")
    parsed = json.loads(result)
    assert "style_guidelines" in parsed


def test_cv_improvement_prompt():
    result = get_cv_improvement_prompt(fmt="json")
    parsed = json.loads(result)
    assert "constraints" in parsed


def test_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported prompt format"):
        get_sop_outline_prompt(fmt="xml")
