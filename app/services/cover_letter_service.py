"""Cover letter generation (single LLM call) with sanitisation and persistence."""

import time
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.llm.prompts import get_cover_letter_prompt
from app.llm.schemas import CoverLetterOutput
from app.models.cover_letter_models import CoverLetterGenerateRequest, CoverLetterResponse
from app.repositories.mysql_cover_letter_repo import CoverLetterRepository
from app.security.input_sanitizer import sanitize_dict, sanitize_text
from app.security.prompt_guardrails import wrap_user_data
from app.services.llm_pipeline_service import LLMPipelineService
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)

PROMPT_VERSION = "cover_letter_v1"


class CoverLetterService:
    """Builds a tailored cover letter from profile + target context."""

    def __init__(
        self,
        llm: LLMPipelineService | None = None,
        repo: CoverLetterRepository | None = None,
    ):
        self._llm = llm or LLMPipelineService()
        self._repo = repo or CoverLetterRepository()

    async def generate(  # pylint: disable=too-many-locals
        self, request: CoverLetterGenerateRequest
    ) -> CoverLetterResponse:
        if settings.USE_MOCK_DATA:
            return await self._mock(request)

        t0 = time.perf_counter()
        profile = sanitize_dict(dict(request.user_profile))
        target = sanitize_dict(dict(request.target_details))

        ctx: dict[str, Any] = {
            "target_type": request.target_type,
            "target_id": request.target_id,
        }
        spec = get_cover_letter_prompt(context=ctx, fmt="text")
        user_block = wrap_user_data({"user_profile": profile, "target_details": target}, label="CONTEXT")
        if request.refinement_instructions:
            note = sanitize_text(request.refinement_instructions, "refinement_instructions")
            user_block += f"\n\nREFINEMENT:\n{note}"
        user_content = (
            user_block + '\n\nRespond with JSON only: {"content": string, "word_count": number, '
            '"tone_assessment": string}.'
        )

        letter_id = generate_uuid()
        res = await self._llm.generate(
            system_prompt=spec,
            user_content=user_content,
            operation="cover_letter_generate",
            max_tokens=1200,
            response_format="json",
            cover_letter_id=letter_id,
        )
        payload = res["content"] if isinstance(res["content"], dict) else {}
        meta = res["metadata"]
        try:
            parsed = CoverLetterOutput.model_validate(payload)
            text = parsed.content
            word_count = parsed.word_count or len(text.split())
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("cover_letter_parse_failed", error=str(exc))
            text = str(payload.get("content") or "")
            word_count = len(text.split())

        version = 1
        if request.parent_letter_id:
            parent = await self._repo.get_by_id(request.parent_letter_id)
            if parent:
                version = int(parent.get("version") or 1) + 1

        elapsed = int((time.perf_counter() - t0) * 1000)
        fallback = meta.get("llm_provider") == "anthropic"

        row = {
            "id": letter_id,
            "user_id": request.user_id,
            "target_type": request.target_type,
            "target_id": request.target_id,
            "version": version,
            "parent_letter_id": request.parent_letter_id,
            "content": text,
            "word_count": word_count,
            "llm_model_used": meta.get("model_name"),
            "llm_fallback_used": fallback,
            "total_processing_time_ms": elapsed,
            "prompt_version": PROMPT_VERSION,
        }

        if not settings.ALLOW_DB_FAILURE:
            await self._repo.create(row)

        return CoverLetterResponse(
            id=letter_id,
            user_id=request.user_id,
            target_type=request.target_type,
            target_id=request.target_id,
            version=version,
            content=text,
            word_count=word_count,
            llm_model_used=meta.get("model_name"),
            llm_fallback_used=fallback,
            total_processing_time_ms=elapsed,
            created_at=None,
            updated_at=None,
        )

    async def _mock(self, request: CoverLetterGenerateRequest) -> CoverLetterResponse:
        t0 = time.perf_counter()
        letter_id = generate_uuid()
        text = (
            "Mock cover letter generated with USE_MOCK_DATA=true. "
            "Replace with real LLM output when integrating prompts."
        )
        word_count = len(text.split())
        version = 1
        if request.parent_letter_id and not settings.ALLOW_DB_FAILURE:
            parent = await self._repo.get_by_id(request.parent_letter_id)
            if parent:
                version = int(parent.get("version") or 1) + 1
        elapsed = int((time.perf_counter() - t0) * 1000)
        row = {
            "id": letter_id,
            "user_id": request.user_id,
            "target_type": request.target_type,
            "target_id": request.target_id,
            "version": version,
            "parent_letter_id": request.parent_letter_id,
            "content": text,
            "word_count": word_count,
            "llm_model_used": "mock",
            "llm_fallback_used": False,
            "total_processing_time_ms": elapsed,
            "prompt_version": PROMPT_VERSION,
        }
        if not settings.ALLOW_DB_FAILURE:
            await self._repo.create(row)
        return CoverLetterResponse(
            id=letter_id,
            user_id=request.user_id,
            target_type=request.target_type,
            target_id=request.target_id,
            version=version,
            content=text,
            word_count=word_count,
            llm_model_used="mock",
            llm_fallback_used=False,
            total_processing_time_ms=elapsed,
            created_at=None,
            updated_at=None,
        )
