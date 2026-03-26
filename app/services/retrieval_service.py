"""Lightweight retrieval service for SOP style references.

Uses metadata-based filtering (NOT full vector RAG) to find
1-2 example SOPs that match the student's field and degree level.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)

# NOTE: Full service implementation is deferred to the next development phase.
# This service should:
#   1. Accept field_of_study, degree_level, program_type
#   2. Query RetrievalRepository for matching references
#   3. Return reference content for injection into SOP prompts
#   4. Respect RETRIEVAL_ENABLED and RETRIEVAL_TOP_K settings
