"""SOP CRUD repository with versioning support."""

import json
from typing import Any

from app.core.logging import get_logger
from app.repositories.mysql_base import MySQLBaseRepository

logger = get_logger(__name__)


def _json_param(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return value


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
            _json_param(sop_data.get("quality_feedback")),
            _json_param(sop_data.get("outline")),
            sop_data.get("expanded_content"),
            sop_data.get("llm_model_used"),
            sop_data.get("llm_fallback_used", False),
            sop_data.get("total_processing_time_ms"),
            sop_data.get("prompt_version"),
            _json_param(sop_data.get("retrieved_reference_ids")),
        )
        await self.execute_write(query, params)
        return sop_data["id"]

    async def get_by_id(self, sop_id: str) -> dict[str, Any] | None:
        """Retrieve a single SOP by ID."""
        query = f"SELECT * FROM {self.TABLE} WHERE id = %s"
        return await self.execute_one(query, (sop_id,))

    async def get_versions(self, sop_id: str) -> list[dict[str, Any]]:
        """Retrieve ancestors, the record itself, and all descendants in the version chain."""
        root = await self.get_by_id(sop_id)
        if not root:
            return []

        seen: dict[str, dict[str, Any]] = {}

        cur: dict[str, Any] | None = root
        while cur:
            seen[cur["id"]] = cur
            pid = cur.get("parent_sop_id")
            cur = await self.get_by_id(pid) if pid else None

        queue: list[str] = [sop_id]
        while queue:
            cid = queue.pop(0)
            children = await self.execute_query(
                f"SELECT * FROM {self.TABLE} WHERE parent_sop_id = %s",
                (cid,),
            )
            for ch in children:
                cid_ch = ch["id"]
                if cid_ch not in seen:
                    seen[cid_ch] = ch
                    queue.append(cid_ch)

        rows = list(seen.values())
        rows.sort(key=lambda r: (r.get("version") or 0, str(r.get("created_at") or "")))
        return rows

    async def get_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        """Retrieve SOPs for a user, paginated."""
        query = f"""
            SELECT * FROM {self.TABLE}
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return await self.execute_query(query, (user_id, limit, offset))
