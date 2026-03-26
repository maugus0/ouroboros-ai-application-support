"""Multi-step SOP generation pipeline using LangGraph.

Pipeline stages:
    1. generate_outline — create a structured SOP outline
    2. expand_outline  — expand outline into full prose
    3. quality_review  — review and refine for quality

This module defines the pipeline graph. Actual LLM calls are delegated
to ``app.services.llm_pipeline_service.LLMPipelineService``.
"""

from app.core.logging import get_logger

logger = get_logger(__name__)

# NOTE: Full LangGraph pipeline implementation is deferred to the
# service layer integration phase. The pipeline state model is defined
# in app.llm.pipeline.state and the prompt templates are in prompts/.
#
# Developer: Wire up LangGraph StateGraph here using:
#   - app.llm.pipeline.state.SOPPipelineState
#   - app.llm.prompts.get_sop_outline_prompt
#   - app.llm.prompts.get_sop_expansion_prompt
#   - app.llm.prompts.get_sop_quality_review_prompt
