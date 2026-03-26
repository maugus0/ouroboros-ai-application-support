"""Persist LLM call audit rows to ``llm_call_logs``."""

from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


class LLMCallLogRepository(MySQLBaseRepository):
    """Raw SQL data access for the llm_call_logs table."""

    TABLE = "llm_call_logs"

    async def create(self, row: dict[str, Any]) -> str:
        """Insert a log row. Returns the log id."""
        query = f"""
            INSERT INTO {self.TABLE}
            (id, operation, sop_id, cover_letter_id, llm_provider, model_name,
             input_tokens, output_tokens, total_cost_usd, latency_ms,
             success, error_message, retry_count, trace_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            row["id"],
            row["operation"],
            row.get("sop_id"),
            row.get("cover_letter_id"),
            row["llm_provider"],
            row["model_name"],
            row.get("input_tokens"),
            row.get("output_tokens"),
            row.get("total_cost_usd"),
            row.get("latency_ms"),
            row["success"],
            row.get("error_message"),
            row.get("retry_count", 0),
            row["trace_id"],
        )
        await self.execute_write(query, params)
        return row["id"]
