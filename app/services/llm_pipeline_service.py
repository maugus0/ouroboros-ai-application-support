"""Multi-step LLM pipeline service with provider fallback.

Provides a unified interface for calling OpenAI (primary) or
Anthropic (fallback) with retry logic and call logging.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)

# NOTE: Full service implementation is deferred to the next development phase.
# This service should:
#   1. Accept a prompt + operation name
#   2. Try OpenAI first, fall back to Anthropic on failure
#   3. Track tokens, cost, and latency for each call
#   4. Return content + metadata dict
#   5. Log every call to llm_call_logs table
