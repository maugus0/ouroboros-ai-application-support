"""Validate LLM outputs for quality, length, safety, and program relevance."""

import re
from typing import Any

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Substring clichés (legacy + extra).
GENERIC_PHRASES = [
    "passionate about",
    "from a young age",
    "throughout my academic journey",
    "I am writing to express my interest",
    "sincerely hope",
    "given the opportunity",
    "perfect fit",
    "dream university",
    "opportunity of a lifetime",
    "ever since I was a child",
    "ignite my passion",
]

# Word-boundary clichés (fewer false positives than bare substring).
GENERIC_PHRASE_REGEXES = [
    re.compile(r"\bdeeply\s+passionate\b", re.IGNORECASE),
    re.compile(r"\btransformative\s+experience\b", re.IGNORECASE),
    re.compile(r"\bunique\s+opportunity\b", re.IGNORECASE),
    re.compile(r"\bworld[\s-]class\b", re.IGNORECASE),
    re.compile(r"\bleading\s+institution\b", re.IGNORECASE),
]

PROMPT_LEAKAGE_PATTERNS = [
    r"\bas an ai\b",
    r"\bi cannot\b",
    r"\bi don't have access\b",
    r"\bi'm unable to\b",
    r"\buser_data section\b",
    r"\bsystem instructions\b",
    r"===== ",
    r"<\|.*?\|>",
    r"\[INST\]",
    r"<\|im_start\|>",
    r"treat as data only",
    r"STUDENT_CONTEXT",
    r"SOP_REVIEW_CONTEXT",
]

# Patterns that suggest the model echoed jailbreak / instruction text.
OUTPUT_INJECTION_PATTERNS = [
    r"ignore (all |previous )?instructions",
    r"disregard (all |previous )?instructions",
    r"you are now (a |an )?",
    r"new task:",
    r"developer mode",
    r"jailbreak",
    r"<\|assistant\|>",
    r"<\|system\|>",
]

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _relevance_strings(target_program: dict[str, Any], program_id: str | None) -> list[str]:
    """Collect distinctive substrings the SOP should mention (school, program, field)."""
    keys = (
        "program_name",
        "name",
        "university_name",
        "university",
        "program_title",
        "field_of_study",
    )
    seen: set[str] = set()
    out: list[str] = []
    for key in keys:
        raw = str(target_program.get(key) or "").strip()
        if len(raw) < 2:
            continue
        if len(raw) == 2 and not raw.isalpha():
            continue
        low = raw.lower()
        if low not in seen:
            seen.add(low)
            out.append(low)
    pid = (program_id or "").strip()
    if pid and not _UUID_RE.match(pid) and len(pid) >= 3:
        pl = pid.lower()
        if pl not in seen:
            out.append(pl)
    return out


def _text_mentions_reference(haystack_lower: str, ref_lower: str) -> bool:
    """Short alphabetic tokens must match as whole words; longer refs use substring match."""
    if len(ref_lower) <= 4 and ref_lower.isalpha():
        return bool(re.search(rf"\b{re.escape(ref_lower)}\b", haystack_lower, re.IGNORECASE))
    return ref_lower in haystack_lower


def check_program_relevance(
    content: str, target_program: dict[str, Any], program_id: str | None = None
) -> tuple[bool, str | None]:
    """Return (ok, issue_message) if the draft plausibly discusses the target program."""
    if not content or not content.strip():
        return False, "Content is empty"
    refs = _relevance_strings(target_program, program_id)
    if not refs:
        return True, None
    hay = content.lower()
    for ref in refs:
        if _text_mentions_reference(hay, ref):
            return True, None
    preview = ", ".join(refs[:3])
    return False, f"Output does not reference expected program context (e.g. {preview})"


def validate_sop(
    content: str,
    min_words: int | None = None,
    max_words: int | None = None,
    *,
    target_program: dict[str, Any] | None = None,
    program_id: str | None = None,
) -> tuple[bool, list[str]]:
    """Validate SOP content: length, clichés, leakage, injection echoes, program relevance."""
    issues: list[str] = []

    if not content or not content.strip():
        return False, ["Content is empty"]

    word_count = len(content.split())
    min_w = min_words or settings.SOP_MIN_WORDS
    max_w = max_words or settings.SOP_MAX_WORDS

    if word_count < min_w:
        issues.append(f"Too short: {word_count} words (minimum {min_w})")
    elif word_count > max_w:
        issues.append(f"Too long: {word_count} words (maximum {max_w})")

    low = content.lower()
    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase.lower() in low)
    generic_count += sum(1 for rx in GENERIC_PHRASE_REGEXES if rx.search(content))
    if generic_count >= 3:
        issues.append(f"Contains {generic_count} generic or template-like phrases (reduce cliches)")

    for pattern in PROMPT_LEAKAGE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Potential prompt leakage detected: '{pattern}'")
            logger.error("prompt_leakage_in_output", pattern=pattern, content_sample=content[:200])

    for pattern in OUTPUT_INJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Potential injected instruction echoed in output: '{pattern}'")
            logger.warning("output_injection_pattern", pattern=pattern, content_sample=content[:200])

    rel_ok, rel_msg = check_program_relevance(content, target_program or {}, program_id)
    if not rel_ok and rel_msg:
        issues.append(rel_msg)

    is_valid = len(issues) == 0
    return is_valid, issues


def compute_quality_score(
    content: str,
    target_program: dict[str, Any] | None = None,
    program_id: str | None = None,
) -> float:
    """Compute a quality score (0.0-1.0) for generated content."""
    score = 1.0

    word_count = len(content.split())
    if word_count < settings.SOP_MIN_WORDS:
        score -= 0.3
    elif word_count > settings.SOP_MAX_WORDS:
        score -= 0.2

    low = content.lower()
    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase.lower() in low)
    generic_count += sum(1 for rx in GENERIC_PHRASE_REGEXES if rx.search(content))
    score -= min(0.3, generic_count * 0.08)

    for pattern in PROMPT_LEAKAGE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            score -= 0.15
            break

    for pattern in OUTPUT_INJECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            score -= 0.2
            break

    rel_ok, _ = check_program_relevance(content, target_program or {}, program_id)
    if not rel_ok:
        score -= 0.15

    sentences = re.split(r"[.!?]+", content)
    if len(sentences) > 5:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length < 10:
            score -= 0.1
        elif avg_sentence_length > 40:
            score -= 0.1

    return max(0.0, min(1.0, score))
