"""Input sanitization to prevent prompt injection and malicious content."""

import re
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import PromptInjectionError, ValidationError

logger = get_logger(__name__)

CONTROL_PATTERNS = [
    r"<\|.*?\|>",
    r"###\s*SYSTEM",
    r"###\s*ASSISTANT",
    r"###\s*IGNORE",
    r"IGNORE\s+(PREVIOUS|ALL)\s+INSTRUCTIONS",
    r"DISREGARD\s+(PREVIOUS|ALL)\s+INSTRUCTIONS",
    r"OVERRIDE\s+SYSTEM",
    r"<.*?>",
]


def sanitize_text(text: str, field_name: str = "input") -> str:
    """Sanitize text input.

    Args:
        text: Raw text from user
        field_name: Field name for logging

    Returns:
        Cleaned text

    Raises:
        ValidationError: If input is too long
        PromptInjectionError: If control instructions are detected
    """
    if not text:
        return text

    if len(text) > settings.MAX_INPUT_LENGTH:
        raise ValidationError(f"{field_name} exceeds maximum length of {settings.MAX_INPUT_LENGTH} characters")

    text = re.sub(r"\s+", " ", text).strip()

    if settings.ENABLE_PROMPT_INJECTION_DETECTION:
        for pattern in CONTROL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(
                    "potential_prompt_injection_detected",
                    field=field_name,
                    pattern=pattern,
                    text_sample=text[:200],
                )
                raise PromptInjectionError(
                    f"{field_name} contains suspicious patterns that may attempt prompt injection"
                )

    return text


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize all text fields in a dictionary."""
    sanitized: dict[str, Any] = {}

    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_text(value, field_name=key)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_text(item, field_name=key) if isinstance(item, str) else item for item in value]
        else:
            sanitized[key] = value

    return sanitized
