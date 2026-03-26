"""Metadata-filtered retrieval of example SOPs for style reference (not vector RAG)."""

from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.repositories.mysql_retrieval_repo import RetrievalRepository

logger = get_logger(__name__)


class RetrievalService:
    """Lightweight style-reference lookup via ``sop_references`` metadata."""

    def __init__(self, repo: RetrievalRepository | None = None):
        self._repo = repo or RetrievalRepository()

    async def fetch_references(
        self,
        *,
        field_of_study: str | None = None,
        degree_level: str | None = None,
        program_type: str | None = None,
    ) -> list[dict[str, Any]]:
        if not settings.RETRIEVAL_ENABLED:
            return []
        limit = max(1, min(settings.RETRIEVAL_TOP_K, 5))
        try:
            rows = await self._repo.find_references(
                field_of_study=field_of_study,
                degree_level=degree_level,
                program_type=program_type,
                quality_rating="excellent",
                limit=limit,
            )
            if not rows:
                rows = await self._repo.find_references(
                    field_of_study=field_of_study,
                    degree_level=degree_level,
                    program_type=program_type,
                    quality_rating="good",
                    limit=limit,
                )
            return rows
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("retrieval_query_failed", error=str(exc))
            return []
