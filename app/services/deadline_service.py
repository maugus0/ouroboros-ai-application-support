"""Thin service layer over ``DeadlineRepository``."""

from app.config import settings
from app.core.logging import get_logger
from app.models.deadline_models import DeadlineCreateRequest, DeadlineResponse, DeadlineUpdateRequest
from app.repositories.mysql_deadline_repo import DeadlineRepository
from app.utils.db_rows import deadline_row_to_dict
from app.utils.exceptions import NotFoundError
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)


class DeadlineService:
    """CRUD-style helpers for deadline entries."""

    def __init__(self, repo: DeadlineRepository | None = None):
        self._repo = repo or DeadlineRepository()

    async def create(self, request: DeadlineCreateRequest) -> DeadlineResponse:
        deadline_id = generate_uuid()
        row = {
            "id": deadline_id,
            "user_id": request.user_id,
            "checklist_id": request.checklist_id,
            "deadline_date": request.deadline_date,
            "deadline_time": request.deadline_time,
            "item_description": request.item_description,
            "item_category": request.item_category,
            "priority": request.priority,
        }
        if not settings.ALLOW_DB_FAILURE:
            await self._repo.create(row)
            stored = await self._repo.get_by_id(deadline_id)
        else:
            stored = {**row, "status": "pending", "reminder_sent": False, "reminder_sent_at": None}
        return DeadlineResponse(**deadline_row_to_dict(stored))

    async def get_by_id(self, deadline_id: str) -> DeadlineResponse:
        if settings.ALLOW_DB_FAILURE:
            raise NotFoundError("Deadline")
        row = await self._repo.get_by_id(deadline_id)
        if not row:
            raise NotFoundError("Deadline")
        return DeadlineResponse(**deadline_row_to_dict(row))

    async def list_for_user(self, user_id: str) -> list[DeadlineResponse]:
        if settings.ALLOW_DB_FAILURE:
            return []
        rows = await self._repo.get_by_user(user_id)
        return [DeadlineResponse(**deadline_row_to_dict(r)) for r in rows]

    async def update(self, deadline_id: str, update: DeadlineUpdateRequest) -> DeadlineResponse:
        if settings.ALLOW_DB_FAILURE:
            raise NotFoundError("Deadline")
        existing = await self._repo.get_by_id(deadline_id)
        if not existing:
            raise NotFoundError("Deadline")

        payload = update.model_dump(exclude_none=True)
        if not payload:
            return DeadlineResponse(**deadline_row_to_dict(existing))

        await self._repo.update(deadline_id, payload)
        row = await self._repo.get_by_id(deadline_id)
        if not row:
            raise NotFoundError("Deadline")
        return DeadlineResponse(**deadline_row_to_dict(row))

    async def upcoming(self, user_id: str, days_ahead: int = 7) -> list[DeadlineResponse]:
        if settings.ALLOW_DB_FAILURE:
            return []
        rows = await self._repo.get_upcoming(user_id, days_ahead=days_ahead)
        return [DeadlineResponse(**deadline_row_to_dict(r)) for r in rows]
