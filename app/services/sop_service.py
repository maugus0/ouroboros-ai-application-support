"""SOP generation orchestration (outline → expand → quality review)."""

import json
import time
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.llm.prompts import get_sop_expansion_prompt, get_sop_outline_prompt, get_sop_quality_review_prompt
from app.llm.schemas import SOPQualityReviewOutput
from app.llm.sop_prompt_bundle import SOP_PROMPT_BUNDLE_ID
from app.models.sop_models import SOPGenerateRequest, SOPResponse
from app.repositories.mysql_sop_repo import SOPRepository
from app.security.input_sanitizer import sanitize_dict
from app.security.output_validator import compute_quality_score, validate_sop
from app.security.prompt_guardrails import wrap_user_data
from app.services.llm_pipeline_service import LLMPipelineService
from app.services.retrieval_service import RetrievalService
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)

PROMPT_VERSION = SOP_PROMPT_BUNDLE_ID


class SOPService:
    """Coordinates sanitisation, retrieval, LLM pipeline, validation, and persistence."""

    def __init__(
        self,
        llm: LLMPipelineService | None = None,
        sop_repo: SOPRepository | None = None,
        retrieval: RetrievalService | None = None,
    ):
        self._llm = llm or LLMPipelineService()
        self._repo = sop_repo or SOPRepository()
        self._retrieval = retrieval or RetrievalService()

    async def generate(  # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        self, request: SOPGenerateRequest
    ) -> SOPResponse:
        if settings.USE_MOCK_DATA:
            return await self._generate_mock(request)

        t0 = time.perf_counter()
        profile = sanitize_dict(dict(request.user_profile))
        target = sanitize_dict(dict(request.target_program))
        prefs = sanitize_dict(dict(request.user_preferences))
        attribution = sanitize_dict(dict(request.match_attribution)) if request.match_attribution else {}
        if request.refinement_instructions:
            prefs = {**prefs, "refinement_instructions": request.refinement_instructions}

        refs = await self._retrieval.fetch_references(
            field_of_study=target.get("field_of_study"),
            degree_level=target.get("degree_level"),
            program_type=target.get("program_type"),
        )
        ref_ids = [r["id"] for r in refs if r.get("id")]

        outline_ctx: dict[str, Any] = {
            "reference_snippets": [str(r.get("content", ""))[:1200] for r in refs],
        }
        outline_spec = get_sop_outline_prompt(context=outline_ctx, fmt="text")
        outline_payload = {
            "user_profile": profile,
            "target_program": target,
            "user_preferences": prefs,
            "match_attribution": attribution,
        }
        outline_user = (
            wrap_user_data(outline_payload)
            + "\n\nRespond with JSON only with keys: introduction_theme (string), body_points (array of strings), "
            "conclusion_theme (string), suggested_tone (string)."
        )

        sop_id = generate_uuid()
        any_fallback = False
        last_model: str | None = None

        outline_res = await self._llm.generate(
            system_prompt=outline_spec,
            user_content=outline_user,
            operation="sop_outline",
            max_tokens=900,
            response_format="json",
            sop_id=sop_id,
        )
        outline_dict = outline_res["content"] if isinstance(outline_res["content"], dict) else {}
        meta_o = outline_res["metadata"]
        if meta_o.get("llm_provider") == "anthropic":
            any_fallback = True
        last_model = meta_o.get("model_name")

        expansion_ctx = {
            "outline": json.dumps(outline_dict, ensure_ascii=False, default=str),
            "user_profile": profile,
            "target_program": target,
            "target_word_count": min(settings.SOP_MAX_WORDS, max(settings.SOP_MIN_WORDS, 650)),
            "min_words": settings.SOP_MIN_WORDS,
            "max_words": settings.SOP_MAX_WORDS,
        }
        expansion_spec = get_sop_expansion_prompt(context=expansion_ctx, fmt="text")
        expansion_user = (
            wrap_user_data(
                {
                    "user_profile": profile,
                    "target_program": target,
                    "user_preferences": prefs,
                    "match_attribution": attribution,
                },
                label="STUDENT_CONTEXT",
            )
            + "\n\nTASK: Write the full Statement of Purpose as plain text (no JSON). Follow the specification."
        )

        exp_res = await self._llm.generate(
            system_prompt=expansion_spec,
            user_content=expansion_user,
            operation="sop_expand",
            max_tokens=1800,
            response_format="text",
            sop_id=sop_id,
        )
        expanded_text = str(exp_res["content"] or "")
        meta_e = exp_res["metadata"]
        if meta_e.get("llm_provider") == "anthropic":
            any_fallback = True
        last_model = meta_e.get("model_name")

        quality_ctx = {
            "content": expanded_text,
            "min_words": settings.SOP_MIN_WORDS,
            "max_words": settings.SOP_MAX_WORDS,
        }
        quality_spec = get_sop_quality_review_prompt(context=quality_ctx, fmt="text")
        quality_user = (
            wrap_user_data(
                {"draft": expanded_text, "match_attribution": attribution},
                label="SOP_REVIEW_CONTEXT",
            )
            + "\n\nReturn JSON with keys: revised_content (string), quality_score (number 0-1), "
            "feedback (array of strings), word_count (integer)."
        )

        q_res = await self._llm.generate(
            system_prompt=quality_spec,
            user_content=quality_user,
            operation="sop_quality_review",
            max_tokens=1200,
            response_format="json",
            sop_id=sop_id,
        )
        q_payload = q_res["content"] if isinstance(q_res["content"], dict) else {}
        meta_q = q_res["metadata"]
        if meta_q.get("llm_provider") == "anthropic":
            any_fallback = True
        last_model = meta_q.get("model_name")

        quality_parse_failed = False
        try:
            review = SOPQualityReviewOutput.model_validate(q_payload)
            final_text = review.revised_content or expanded_text
            quality_score = float(review.quality_score)
            feedback = list(review.feedback or [])
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("quality_review_parse_failed", error=str(exc))
            quality_parse_failed = True
            final_text = expanded_text
            quality_score = compute_quality_score(
                expanded_text,
                target_program=target,
                program_id=request.program_id,
            )
            feedback = []

        if settings.ENABLE_OUTPUT_VALIDATION:
            ok, issues = validate_sop(
                final_text,
                target_program=target,
                program_id=request.program_id,
            )
            if not ok:
                feedback = list(feedback) + issues
            if quality_parse_failed:
                note = "LLM quality review could not be parsed; score is heuristic."
                feedback = [note] + list(feedback) if feedback else [note]
            if not ok:
                quality_score = min(
                    float(quality_score),
                    compute_quality_score(
                        final_text,
                        target_program=target,
                        program_id=request.program_id,
                    ),
                )
        elif quality_parse_failed:
            feedback = ["LLM quality review could not be parsed; score is heuristic."]

        version = 1
        if request.parent_sop_id and not settings.ALLOW_DB_FAILURE:
            parent = await self._repo.get_by_id(request.parent_sop_id)
            if parent:
                version = int(parent.get("version") or 1) + 1

        word_count = len(final_text.split())
        elapsed_ms = int((time.perf_counter() - t0) * 1000)

        row = {
            "id": sop_id,
            "user_id": request.user_id,
            "program_id": request.program_id,
            "version": version,
            "parent_sop_id": request.parent_sop_id,
            "content": final_text,
            "word_count": word_count,
            "quality_score": quality_score,
            "quality_feedback": feedback,
            "outline": outline_dict,
            "expanded_content": expanded_text,
            "llm_model_used": last_model,
            "llm_fallback_used": any_fallback,
            "total_processing_time_ms": elapsed_ms,
            "prompt_version": PROMPT_VERSION,
            "retrieved_reference_ids": ref_ids,
            "match_attribution_snapshot": attribution or None,
        }

        if not settings.ALLOW_DB_FAILURE:
            await self._repo.create(row)

        return SOPResponse(
            id=sop_id,
            user_id=request.user_id,
            program_id=request.program_id,
            version=version,
            content=final_text,
            word_count=word_count,
            quality_score=quality_score,
            quality_feedback=feedback or None,
            match_attribution_snapshot=attribution or None,
            llm_model_used=last_model,
            llm_fallback_used=any_fallback,
            total_processing_time_ms=elapsed_ms,
            created_at=None,
            updated_at=None,
        )

    async def _generate_mock(self, request: SOPGenerateRequest) -> SOPResponse:
        sanitize_dict(dict(request.user_profile))
        sanitize_dict(dict(request.target_program))
        prefs = dict(request.user_preferences)
        if request.refinement_instructions:
            prefs = {**prefs, "refinement_instructions": request.refinement_instructions}
        sanitize_dict(prefs)
        t0 = time.perf_counter()
        sop_id = generate_uuid()
        body = (
            "This is mock Statement of Purpose content generated with USE_MOCK_DATA=true. "
            "It exists so CI and local development can exercise the API without calling an LLM. "
        )
        final_text = (" ".join([body] * 20)).strip()
        word_count = len(final_text.split())
        version = 1
        if request.parent_sop_id:
            parent = await self._repo.get_by_id(request.parent_sop_id) if not settings.ALLOW_DB_FAILURE else None
            if parent:
                version = int(parent.get("version") or 1) + 1

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        outline_dict = {
            "introduction_theme": "mock",
            "body_points": ["mock_point"],
            "conclusion_theme": "mock",
            "suggested_tone": "professional",
        }
        mock_attr = sanitize_dict(dict(request.match_attribution)) if request.match_attribution else {}
        row = {
            "id": sop_id,
            "user_id": request.user_id,
            "program_id": request.program_id,
            "version": version,
            "parent_sop_id": request.parent_sop_id,
            "content": final_text,
            "word_count": word_count,
            "quality_score": 0.85,
            "quality_feedback": ["mock feedback"],
            "outline": outline_dict,
            "expanded_content": final_text,
            "llm_model_used": "mock",
            "llm_fallback_used": False,
            "total_processing_time_ms": elapsed_ms,
            "prompt_version": PROMPT_VERSION,
            "retrieved_reference_ids": [],
            "match_attribution_snapshot": mock_attr or None,
        }
        if not settings.ALLOW_DB_FAILURE:
            await self._repo.create(row)

        return SOPResponse(
            id=sop_id,
            user_id=request.user_id,
            program_id=request.program_id,
            version=version,
            content=final_text,
            word_count=word_count,
            quality_score=0.85,
            quality_feedback=["mock feedback"],
            match_attribution_snapshot=mock_attr or None,
            llm_model_used="mock",
            llm_fallback_used=False,
            total_processing_time_ms=elapsed_ms,
            created_at=None,
            updated_at=None,
        )
