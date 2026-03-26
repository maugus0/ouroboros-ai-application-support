"""SOP reference retrieval repository for style guidance."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


class RetrievalRepository(MySQLBaseRepository):
    """Raw SQL data access for the sop_references table (metadata-based filtering, not vector search)."""

    TABLE = "sop_references"

    async def find_references(
        self,
        field_of_study: str | None = None,
        degree_level: str | None = None,
        program_type: str | None = None,
        quality_rating: str = "excellent",
        limit: int = 2,
    ) -> list[dict[str, Any]]:
        """Find SOP references matching the given criteria.

        Uses metadata filtering (field, degree, program type) rather
        than vector similarity. Returns top-K results ordered by quality.
        """
        conditions = ["quality_rating = %s"]
        params: list[Any] = [quality_rating]

        if field_of_study:
            conditions.append("field_of_study = %s")
            params.append(field_of_study)
        if degree_level:
            conditions.append("degree_level = %s")
            params.append(degree_level)
        if program_type:
            conditions.append("program_type = %s")
            params.append(program_type)

        where_clause = " AND ".join(conditions)
        params.append(limit)

        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT %s
        """
        return await self.execute_query(query, tuple(params))

    async def get_by_id(self, reference_id: str) -> dict[str, Any] | None:
        """Retrieve a single SOP reference by ID."""
        query = f"SELECT * FROM {self.TABLE} WHERE id = %s"
        return await self.execute_one(query, (reference_id,))
