"""Validate LLM outputs for quality, length, and safety."""

import re

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

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
]

PROMPT_LEAKAGE_PATTERNS = [
    r"as an ai",
    r"i cannot",
    r"i don't have access",
    r"i'm unable to",
    r"user_data section",
    r"system instructions",
    r"===== ",
]


def validate_sop(
    content: str,
    min_words: int | None = None,
    max_words: int | None = None,
) -> tuple[bool, list[str]]:
    """Validate SOP content.

    Args:
        content: SOP text
        min_words: Minimum word count (default from settings)
        max_words: Maximum word count (default from settings)

    Returns:
        (is_valid, list_of_issues)
    """
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

    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase.lower() in content.lower())
    if generic_count >= 3:
        issues.append(f"Contains {generic_count} generic phrases (reduce cliches)")

    for pattern in PROMPT_LEAKAGE_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            issues.append(f"Potential prompt leakage detected: '{pattern}'")
            logger.error("prompt_leakage_in_output", pattern=pattern, content_sample=content[:200])

    is_valid = len(issues) == 0
    return is_valid, issues


def compute_quality_score(content: str) -> float:
    """Compute a quality score (0.0-1.0) for generated content.

    Factors:
    - Length appropriateness
    - Generic phrase density
    - Sentence variety

    Returns:
        Quality score between 0.0 and 1.0
    """
    score = 1.0

    word_count = len(content.split())
    if word_count < settings.SOP_MIN_WORDS:
        score -= 0.3
    elif word_count > settings.SOP_MAX_WORDS:
        score -= 0.2

    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase.lower() in content.lower())
    score -= min(0.3, generic_count * 0.1)

    sentences = re.split(r"[.!?]+", content)
    if len(sentences) > 5:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_length < 10:
            score -= 0.1
        elif avg_sentence_length > 40:
            score -= 0.1

    return max(0.0, min(1.0, score))
