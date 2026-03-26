"""Cover letter CRUD repository."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


class CoverLetterRepository(MySQLBaseRepository):
    """Raw SQL data access for the generated_cover_letters table."""

    TABLE = "generated_cover_letters"

    async def create(self, letter_data: dict[str, Any]) -> str:
        """Insert a new cover letter record. Returns the letter ID."""
        query = f"""
            INSERT INTO {self.TABLE}
            (id, user_id, target_type, target_id, version, parent_letter_id,
             content, word_count, llm_model_used, llm_fallback_used,
             total_processing_time_ms, prompt_version)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            letter_data["id"],
            letter_data["user_id"],
            letter_data["target_type"],
            letter_data.get("target_id"),
            letter_data.get("version", 1),
            letter_data.get("parent_letter_id"),
            letter_data["content"],
            letter_data["word_count"],
            letter_data.get("llm_model_used"),
            letter_data.get("llm_fallback_used", False),
            letter_data.get("total_processing_time_ms"),
            letter_data.get("prompt_version"),
        )
        await self.execute_write(query, params)
        return letter_data["id"]

    async def get_by_id(self, letter_id: str) -> dict[str, Any] | None:
        """Retrieve a single cover letter by ID."""
        query = f"SELECT * FROM {self.TABLE} WHERE id = %s"
        return await self.execute_one(query, (letter_id,))

    async def get_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """Retrieve cover letters for a user, paginated."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return await self.execute_query(query, (user_id, limit, offset))
