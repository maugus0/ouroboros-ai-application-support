"""Multi-step LLM calls with OpenAI primary and Anthropic fallback."""

import json
import time
import uuid
from typing import Any, Literal

from app.config import settings
from app.core.logging import get_logger
from app.llm.anthropic_client import call_anthropic
from app.llm.openai_client import call_openai
from app.models.llm_models import LLMCallMetadata
from app.repositories.mysql_llm_call_log_repo import LLMCallLogRepository
from app.utils.exceptions import LLMGenerationError
from app.utils.trace_id import get_bound_trace_id

logger = get_logger(__name__)


class LLMPipelineService:
    """Single-call LLM orchestration with provider fallback and optional audit logging."""

    @staticmethod
    def _parse_content(raw_text: str, response_format: Literal["json", "text"] | None) -> Any:
        if response_format != "json":
            return raw_text
        text = (raw_text or "").strip()
        return json.loads(text)

    async def _persist_log(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        *,
        operation: str,
        sop_id: str | None,
        cover_letter_id: str | None,
        llm_provider: str,
        model_name: str,
        input_tokens: int | None,
        output_tokens: int | None,
        latency_ms: int,
        success: bool,
        error_message: str | None = None,
    ) -> None:
        if settings.ALLOW_DB_FAILURE:
            return
        try:
            repo = LLMCallLogRepository()
            await repo.create(
                {
                    "id": str(uuid.uuid4()),
                    "operation": operation,
                    "sop_id": sop_id,
                    "cover_letter_id": cover_letter_id,
                    "llm_provider": llm_provider,
                    "model_name": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_cost_usd": None,
                    "latency_ms": latency_ms,
                    "success": success,
                    "error_message": error_message,
                    "retry_count": 0,
                    "trace_id": get_bound_trace_id(),
                }
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("llm_call_log_persist_failed", error=str(exc))

    async def generate(  # pylint: disable=too-many-locals
        self,
        *,
        system_prompt: str,
        user_content: str,
        operation: str,
        max_tokens: int,
        response_format: Literal["json", "text"] | None = None,
        sop_id: str | None = None,
        cover_letter_id: str | None = None,
    ) -> dict[str, Any]:
        """Run an LLM call with OpenAI first, then Anthropic.

        Returns:
            ``{"content": str | dict, "metadata": LLMCallMetadata}`` where ``content`` is parsed JSON
            when ``response_format == "json"``, otherwise raw text.
        """
        last_error: str | None = None

        if settings.OPENAI_API_KEY:
            t0 = time.perf_counter()
            try:
                oai_fmt = "json" if response_format == "json" else None
                raw = await call_openai(
                    user_content,
                    system_prompt,
                    max_tokens=max_tokens,
                    response_format=oai_fmt,
                )
                latency_ms = int((time.perf_counter() - t0) * 1000)
                content_str = raw["content"]
                parsed = self._parse_content(content_str, response_format)
                in_tok = int(raw.get("input_tokens") or 0)
                out_tok = int(raw.get("output_tokens") or 0)
                meta = LLMCallMetadata(
                    operation=operation,
                    llm_provider="openai",
                    model_name=str(raw["model"]),
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    total_tokens=int(raw.get("total_tokens") or in_tok + out_tok),
                    latency_ms=latency_ms,
                    success=True,
                )
                await self._persist_log(
                    operation=operation,
                    sop_id=sop_id,
                    cover_letter_id=cover_letter_id,
                    llm_provider="openai",
                    model_name=str(raw["model"]),
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=latency_ms,
                    success=True,
                )
                return {"content": parsed, "metadata": meta.model_dump()}
            except Exception as exc:  # pylint: disable=broad-exception-caught
                last_error = str(exc)
                logger.warning("openai_failed_falling_back_to_anthropic", error=last_error)
                latency_ms = int((time.perf_counter() - t0) * 1000)
                await self._persist_log(
                    operation=operation,
                    sop_id=sop_id,
                    cover_letter_id=cover_letter_id,
                    llm_provider="openai",
                    model_name=settings.OPENAI_MODEL,
                    input_tokens=None,
                    output_tokens=None,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=last_error,
                )

        if settings.ANTHROPIC_API_KEY:
            t1 = time.perf_counter()
            try:
                user_block = user_content
                if response_format == "json":
                    user_block = (
                        user_content + "\n\nRespond with a single valid JSON object only. No markdown fences or prose."
                    )
                raw = await call_anthropic(
                    user_block,
                    system_prompt,
                    max_tokens=max_tokens,
                )
                latency_ms = int((time.perf_counter() - t1) * 1000)
                content_str = raw["content"]
                parsed = self._parse_content(content_str, response_format)
                in_tok = int(raw.get("input_tokens") or 0)
                out_tok = int(raw.get("output_tokens") or 0)
                meta = LLMCallMetadata(
                    operation=operation,
                    llm_provider="anthropic",
                    model_name=str(raw["model"]),
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    total_tokens=in_tok + out_tok,
                    latency_ms=latency_ms,
                    success=True,
                )
                await self._persist_log(
                    operation=operation,
                    sop_id=sop_id,
                    cover_letter_id=cover_letter_id,
                    llm_provider="anthropic",
                    model_name=str(raw["model"]),
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    latency_ms=latency_ms,
                    success=True,
                )
                return {"content": parsed, "metadata": meta.model_dump()}
            except Exception as exc:  # pylint: disable=broad-exception-caught
                err = str(exc)
                logger.error("anthropic_call_failed", error=err)
                latency_ms = int((time.perf_counter() - t1) * 1000)
                await self._persist_log(
                    operation=operation,
                    sop_id=sop_id,
                    cover_letter_id=cover_letter_id,
                    llm_provider="anthropic",
                    model_name=settings.ANTHROPIC_MODEL,
                    input_tokens=None,
                    output_tokens=None,
                    latency_ms=latency_ms,
                    success=False,
                    error_message=err,
                )
                raise LLMGenerationError(f"Both LLM providers failed. Last error: {err}") from exc

        raise LLMGenerationError(
            last_error or "No LLM API key configured (set OPENAI_API_KEY and/or ANTHROPIC_API_KEY)"
        )
