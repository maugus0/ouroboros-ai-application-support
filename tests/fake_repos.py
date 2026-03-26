"""In-memory fake repositories for testing without a database."""

from typing import Any

from app.utils.helpers import generate_uuid, get_current_time_iso


class FakeSOPRepository:
    """In-memory SOP repository for unit tests."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def create(self, sop_data: dict[str, Any]) -> str:
        sop_id = sop_data.get("id", generate_uuid())
        sop_data["id"] = sop_id
        sop_data.setdefault("created_at", get_current_time_iso())
        self._store[sop_id] = sop_data
        return sop_id

    async def get_by_id(self, sop_id: str) -> dict[str, Any] | None:
        return self._store.get(sop_id)

    async def get_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        results = [s for s in self._store.values() if s.get("user_id") == user_id]
        return results[offset : offset + limit]


class FakeDeadlineRepository:
    """In-memory deadline repository for unit tests."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    async def create(self, deadline_data: dict[str, Any]) -> str:
        deadline_id = deadline_data.get("id", generate_uuid())
        deadline_data["id"] = deadline_id
        self._store[deadline_id] = deadline_data
        return deadline_id

    async def get_by_id(self, deadline_id: str) -> dict[str, Any] | None:
        return self._store.get(deadline_id)

    async def get_by_user(self, user_id: str) -> list[dict[str, Any]]:
        return [d for d in self._store.values() if d.get("user_id") == user_id]
