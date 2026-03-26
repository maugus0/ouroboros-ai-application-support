"""Quality scoring logic for generated content.

This module provides quality assessment functions used by the
SOP pipeline's quality review step.
"""

from app.core.logging import get_logger
from app.security.output_validator import compute_quality_score, validate_sop

logger = get_logger(__name__)


def assess_sop_quality(content: str) -> dict:
    """Run quality assessment on SOP content.

    Returns:
        Dict with 'is_valid', 'issues', 'quality_score'.
    """
    is_valid, issues = validate_sop(content)
    score = compute_quality_score(content)

    if not is_valid:
        logger.warning("sop_quality_issues", issues=issues, score=score)

    return {
        "is_valid": is_valid,
        "issues": issues,
        "quality_score": score,
    }
