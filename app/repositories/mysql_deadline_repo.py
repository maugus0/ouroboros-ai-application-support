"""Deadline entries CRUD repository."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


class DeadlineRepository(MySQLBaseRepository):
    """Raw SQL data access for the deadline_entries table."""

    TABLE = "deadline_entries"

    async def create(self, deadline_data: dict[str, Any]) -> str:
        """Insert a new deadline entry. Returns the deadline ID."""
        query = f"""
            INSERT INTO {self.TABLE}
            (id, user_id, checklist_id, source_type, source_id, deadline_date, deadline_time,
             item_description, item_category, priority)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            deadline_data["id"],
            deadline_data["user_id"],
            deadline_data.get("checklist_id"),
            deadline_data.get("source_type", "manual"),
            deadline_data.get("source_id"),
            deadline_data["deadline_date"],
            deadline_data.get("deadline_time"),
            deadline_data["item_description"],
            deadline_data.get("item_category", "application"),
            deadline_data.get("priority", "medium"),
        )
        await self.execute_write(query, params)
        return deadline_data["id"]

    async def get_by_id(self, deadline_id: str) -> dict[str, Any] | None:
        """Retrieve a single deadline by ID."""
        query = f"SELECT * FROM {self.TABLE} WHERE id = %s"
        return await self.execute_one(query, (deadline_id,))

    async def get_by_user(self, user_id: str) -> list[dict[str, Any]]:
        """Retrieve all deadlines for a user, ordered by date."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = %s
            ORDER BY deadline_date ASC, deadline_time ASC
        """
        return await self.execute_query(query, (user_id,))

    async def update(self, deadline_id: str, update_data: dict[str, Any]) -> int:
        """Update a deadline entry with non-null fields."""
        set_clauses = []
        params = []
        for key, value in update_data.items():
            if value is not None:
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return 0

        params.append(deadline_id)
        query = f"UPDATE {self.TABLE} SET {', '.join(set_clauses)} WHERE id = %s"
        return await self.execute_write(query, tuple(params))

    async def get_upcoming(self, user_id: str, days_ahead: int = 7) -> list[dict[str, Any]]:
        """Retrieve deadlines within the next N days."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = %s
              AND status = 'pending'
              AND deadline_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY deadline_date ASC
        """
        return await self.execute_query(query, (user_id, days_ahead))

    async def list_pending_reminder_candidates(self, days: int = 30) -> list[dict[str, Any]]:
        """Deadlines that are pending, not yet flagged, and within the next ``days`` (inclusive)."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE status = 'pending'
              AND reminder_sent = FALSE
              AND deadline_date >= CURDATE()
              AND deadline_date <= DATE_ADD(CURDATE(), INTERVAL %s DAY)
            ORDER BY deadline_date ASC
        """
        return await self.execute_query(query, (days,))

    async def mark_reminder_sent(self, deadline_id: str) -> int:
        """Set reminder flags for one deadline (idempotent if already sent)."""
        query = f"""
            UPDATE {self.TABLE}
            SET reminder_sent = TRUE, reminder_sent_at = CURRENT_TIMESTAMP
            WHERE id = %s AND reminder_sent = FALSE
        """
        return await self.execute_write(query, (deadline_id,))
