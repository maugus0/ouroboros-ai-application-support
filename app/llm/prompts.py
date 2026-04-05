"""Prompt loading and building with runtime context injection.

Templates live under ``prompts/`` as versioned JSON. These helpers are
used by in-process code (e.g. ``LLMPipelineService``), not by HTTP clients.
The Ouroboros orchestrator calls this microservice over HTTP; those
requests are handled in ``app/api`` and eventually invoke services that
build prompts here.

Each function returns a string in the requested format (``json`` or
``text``). Unknown ``fmt`` values raise ``ValueError`` so typos fail
fast at development time.
"""

from typing import Any

from app.llm.sop_prompt_bundle import (
    SOP_EXPANSION_PROMPT_FILE,
    SOP_OUTLINE_PROMPT_FILE,
    SOP_QUALITY_REVIEW_PROMPT_FILE,
)
from app.utils.prompt_utils import build_prompt_json, build_prompt_text

_VALID_FORMATS: frozenset[str] = frozenset({"json", "text"})


def _require_prompt_format(fmt: str) -> None:
    if fmt not in _VALID_FORMATS:
        raise ValueError(f"Unsupported prompt format {fmt!r}; expected one of {sorted(_VALID_FORMATS)}.")


def get_sop_outline_prompt(
    context: dict[str, Any] | None = None,
    fmt: str = "json",
) -> str:
    """Build the SOP outline system prompt (pipeline step 1)."""
    _require_prompt_format(fmt)
    if fmt == "text":
        return build_prompt_text(SOP_OUTLINE_PROMPT_FILE, context)
    return build_prompt_json(SOP_OUTLINE_PROMPT_FILE, context)


def get_sop_expansion_prompt(
    context: dict[str, Any] | None = None,
    fmt: str = "json",
) -> str:
    """Build the SOP expansion system prompt (pipeline step 2)."""
    _require_prompt_format(fmt)
    if fmt == "text":
        return build_prompt_text(SOP_EXPANSION_PROMPT_FILE, context)
    return build_prompt_json(SOP_EXPANSION_PROMPT_FILE, context)


def get_sop_quality_review_prompt(
    context: dict[str, Any] | None = None,
    fmt: str = "json",
) -> str:
    """Build the SOP quality review system prompt (pipeline step 3)."""
    _require_prompt_format(fmt)
    if fmt == "text":
        return build_prompt_text(SOP_QUALITY_REVIEW_PROMPT_FILE, context)
    return build_prompt_json(SOP_QUALITY_REVIEW_PROMPT_FILE, context)


def get_cover_letter_prompt(
    context: dict[str, Any] | None = None,
    fmt: str = "json",
) -> str:
    """Build the cover letter generation system prompt."""
    _require_prompt_format(fmt)
    if fmt == "text":
        return build_prompt_text("cover_letter_generation_v1.json", context)
    return build_prompt_json("cover_letter_generation_v1.json", context)


def get_cv_improvement_prompt(
    context: dict[str, Any] | None = None,
    fmt: str = "json",
) -> str:
    """Build the CV improvement suggestions system prompt."""
    _require_prompt_format(fmt)
    if fmt == "text":
        return build_prompt_text("cv_improvement_v1.json", context)
    return build_prompt_json("cv_improvement_v1.json", context)
