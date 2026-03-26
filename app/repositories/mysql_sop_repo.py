"""SOP CRUD repository with versioning support."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


class SOPRepository(MySQLBaseRepository):
    """Raw SQL data access for the generated_sops table."""

    TABLE = "generated_sops"

    async def create(self, sop_data: dict[str, Any]) -> str:
        """Insert a new SOP record. Returns the SOP ID."""
        query = f"""
            INSERT INTO {self.TABLE}
            (id, user_id, program_id, version, parent_sop_id, content, word_count,
             quality_score, quality_feedback, outline, expanded_content,
             llm_model_used, llm_fallback_used, total_processing_time_ms, prompt_version,
             retrieved_reference_ids)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            sop_data["id"],
            sop_data["user_id"],
            sop_data.get("program_id"),
            sop_data.get("version", 1),
            sop_data.get("parent_sop_id"),
            sop_data["content"],
            sop_data["word_count"],
            sop_data.get("quality_score"),
            sop_data.get("quality_feedback"),
            sop_data.get("outline"),
            sop_data.get("expanded_content"),
            sop_data.get("llm_model_used"),
            sop_data.get("llm_fallback_used", False),
            sop_data.get("total_processing_time_ms"),
            sop_data.get("prompt_version"),
            sop_data.get("retrieved_reference_ids"),
        )
        await self.execute_write(query, params)
        return sop_data["id"]

    async def get_by_id(self, sop_id: str) -> dict[str, Any] | None:
        """Retrieve a single SOP by ID."""
        query = f"SELECT * FROM {self.TABLE} WHERE id = %s"
        return await self.execute_one(query, (sop_id,))

    async def get_versions(self, sop_id: str) -> list[dict[str, Any]]:
        """Retrieve all versions of an SOP (following the parent chain)."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE id = %s OR parent_sop_id = %s
            ORDER BY version ASC
        """
        return await self.execute_query(query, (sop_id, sop_id))

    async def get_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """Retrieve SOPs for a user, paginated."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return await self.execute_query(query, (user_id, limit, offset))
