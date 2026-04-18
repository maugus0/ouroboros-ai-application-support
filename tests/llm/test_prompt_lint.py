"""Tests for structural validity of prompts (Linting)."""

import json
import re

import pytest
import tiktoken

from app.llm.prompts import (
    get_cover_letter_prompt,
    get_cv_improvement_prompt,
    get_sop_expansion_prompt,
    get_sop_outline_prompt,
    get_sop_quality_review_prompt,
)

# Regex to find unrendered variables in prompts like {{ variable_name }}
PLACEHOLDER_PATTERN = re.compile(r"\{\{.*?\}\}")

# Typical limits for models used
OPENAI_LIMIT = 128_000
ANTHROPIC_LIMIT = 200_000

# We consider a prompt too large if it exceeds 80% of the limit
MAX_ALLOWED_TOKENS = int(min(OPENAI_LIMIT, ANTHROPIC_LIMIT) * 0.8)


def get_token_count(text: str, model_name: str = "gpt-4o") -> int:
    """Estimates the token count of the text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")  # default for newer openai models
    return len(encoding.encode(text))


def assert_no_unrendered_placeholders(rendered_text: str) -> None:
    """Ensures that no `{{ placeholder }}` remains in the string after rendering."""
    matches = PLACEHOLDER_PATTERN.findall(rendered_text)
    assert not matches, f"Found unrendered placeholders in prompt: {matches}"


def assert_token_count_within_limit(rendered_text: str) -> None:
    """Ensures the rendered prompt isn't excessively large."""
    tokens = get_token_count(rendered_text)
    assert tokens < MAX_ALLOWED_TOKENS, f"Prompt token count ({tokens}) exceeds safe limit ({MAX_ALLOWED_TOKENS})."


def test_all_prompt_json_files_are_valid_json(all_prompt_files):
    """Ensures all JSON files in the prompts directory can be parsed."""
    assert len(all_prompt_files) > 0, "No prompt files found!"
    for filepath in all_prompt_files:
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as exc:
                pytest.fail(f"Invalid JSON in {filepath.name}: {exc}")


def test_sop_outline_prompt_renders_without_error(mock_sop_context):
    prompt = get_sop_outline_prompt(context=mock_sop_context, fmt="text")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert_no_unrendered_placeholders(prompt)
    assert_token_count_within_limit(prompt)


def test_sop_expansion_prompt_renders_without_error(mock_sop_context):
    prompt = get_sop_expansion_prompt(context=mock_sop_context, fmt="text")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert_no_unrendered_placeholders(prompt)
    assert_token_count_within_limit(prompt)


def test_sop_quality_review_prompt_renders_without_error(mock_sop_context):
    # Add outline to context since review prompt might need it
    ctx = mock_sop_context.copy()
    ctx["draft_content"] = "This is a drafted SOP."
    prompt = get_sop_quality_review_prompt(context=ctx, fmt="text")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert_no_unrendered_placeholders(prompt)
    assert_token_count_within_limit(prompt)


def test_cover_letter_prompt_renders_without_error(mock_cover_letter_context):
    prompt = get_cover_letter_prompt(context=mock_cover_letter_context, fmt="text")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert_no_unrendered_placeholders(prompt)
    assert_token_count_within_limit(prompt)


def test_cv_improvement_prompt_renders_without_error():
    # CV improvement might need different context
    ctx = {"cv_text": "Experienced software engineer with a focus on AI."}
    prompt = get_cv_improvement_prompt(context=ctx, fmt="text")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert_no_unrendered_placeholders(prompt)
    assert_token_count_within_limit(prompt)
