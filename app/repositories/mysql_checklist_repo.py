"""Application checklist CRUD repository."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


class ChecklistRepository(MySQLBaseRepository):
    """Raw SQL data access for the application_checklists table."""

    TABLE = "application_checklists"

    async def create(self, checklist_data: dict[str, Any]) -> str:
        """Insert a new checklist. Returns the checklist ID."""
        query = f"""
            INSERT INTO {self.TABLE}
            (id, user_id, program_id, items, overall_status, completion_percentage)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            checklist_data["id"],
            checklist_data["user_id"],
            checklist_data.get("program_id"),
            checklist_data["items"],
            checklist_data.get("overall_status", "not_started"),
            checklist_data.get("completion_percentage", 0.0),
        )
        await self.execute_write(query, params)
        return checklist_data["id"]

    async def get_by_id(self, checklist_id: str) -> dict[str, Any] | None:
        """Retrieve a single checklist by ID."""
        query = f"SELECT * FROM {self.TABLE} WHERE id = %s"
        return await self.execute_one(query, (checklist_id,))

    async def get_by_user(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieve all checklists for a user."""
        query = f"SELECT * FROM {self.TABLE} WHERE user_id = %s ORDER BY created_at DESC"
        return await self.execute_query(query, (user_id,))

    async def update_items(self, checklist_id: str, items_json: str, status: str, percentage: float) -> int:
        """Update checklist items and recalculate status."""
        query = f"""
            UPDATE {self.TABLE}
            SET items = %s, overall_status = %s, completion_percentage = %s
            WHERE id = %s
        """
        return await self.execute_write(query, (items_json, status, percentage, checklist_id))
