"""Application checklist creation and item updates."""

import json
from typing import Any

from app.config import settings
from app.core.logging import get_logger
from app.models.checklist_models import ChecklistCreateRequest, ChecklistItem, ChecklistResponse
from app.repositories.mysql_checklist_repo import ChecklistRepository
from app.services.checklist_item_builder import build_default_checklist_items
from app.utils.db_rows import checklist_items_for_update, checklist_row_to_dict
from app.utils.exceptions import NotFoundError
from app.utils.helpers import generate_uuid

logger = get_logger(__name__)


class ChecklistService:
    """Creates checklists and recalculates completion metadata on item updates."""

    def __init__(self, repo: ChecklistRepository | None = None):
        self._repo = repo or ChecklistRepository()

    @staticmethod
    def compute_status(items: list[dict[str, Any]]) -> tuple[str, float]:
        total = len(items)
        if total == 0:
            return "not_started", 0.0
        completed = sum(1 for it in items if it.get("status") == "completed")
        in_progress = any(it.get("status") == "in_progress" for it in items)
        pct = round(100.0 * completed / total, 2)
        if completed == total:
            overall = "completed"
        elif completed == 0 and not in_progress:
            overall = "not_started"
        else:
            overall = "in_progress"
        return overall, pct

    async def create_checklist(self, request: ChecklistCreateRequest) -> ChecklistResponse:
        checklist_id = generate_uuid()
        items: list[dict[str, Any]] = []
        if request.items:
            for it in request.items:
                d = it.model_dump()
                if not d.get("id"):
                    d["id"] = generate_uuid()
                items.append(d)
        else:
            for row in build_default_checklist_items(
                request.program_requirements,
                request.target_program,
            ):
                row = dict(row)
                row["id"] = generate_uuid()
                items.append(row)

        overall, pct = self.compute_status(items)

        row = {
            "id": checklist_id,
            "user_id": request.user_id,
            "program_id": request.program_id,
            "items": items,
            "overall_status": overall,
            "completion_percentage": pct,
        }

        if not settings.ALLOW_DB_FAILURE:
            await self._repo.create(row)
            stored = await self._repo.get_by_id(checklist_id)
        else:
            stored = {
                "id": checklist_id,
                "user_id": request.user_id,
                "program_id": request.program_id,
                "items": items,
                "overall_status": overall,
                "completion_percentage": pct,
                "created_at": None,
                "updated_at": None,
            }

        data = checklist_row_to_dict(stored)
        return ChecklistResponse(
            id=data["id"],
            user_id=data["user_id"],
            program_id=data.get("program_id"),
            items=[ChecklistItem(**x) for x in data["items"]],
            overall_status=data["overall_status"],
            completion_percentage=data["completion_percentage"],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    async def list_for_user(self, user_id: str) -> list[ChecklistResponse]:
        if settings.ALLOW_DB_FAILURE:
            return []
        rows = await self._repo.get_by_user(user_id)
        out: list[ChecklistResponse] = []
        for row in rows:
            data = checklist_row_to_dict(row)
            out.append(
                ChecklistResponse(
                    id=data["id"],
                    user_id=data["user_id"],
                    program_id=data.get("program_id"),
                    items=[ChecklistItem(**x) for x in data["items"]],
                    overall_status=data["overall_status"],
                    completion_percentage=data["completion_percentage"],
                    created_at=data.get("created_at"),
                    updated_at=data.get("updated_at"),
                )
            )
        return out

    async def update_item(self, checklist_id: str, item_id: str, new_status: str) -> ChecklistResponse:
        if settings.ALLOW_DB_FAILURE:
            raise NotFoundError("Checklist")

        row = await self._repo.get_by_id(checklist_id)
        if not row:
            raise NotFoundError("Checklist")

        items = checklist_items_for_update(row.get("items"))

        found = False
        for it in items:
            if str(it.get("id")) == str(item_id):
                it["status"] = new_status
                found = True
                break
        if not found:
            raise NotFoundError("Checklist item")

        overall, pct = self.compute_status(items)
        items_json = json.dumps(items, ensure_ascii=False, default=str)
        await self._repo.update_items(checklist_id, items_json, overall, pct)
        updated = await self._repo.get_by_id(checklist_id)
        if not updated:
            raise NotFoundError("Checklist")
        data = checklist_row_to_dict(updated)
        return ChecklistResponse(
            id=data["id"],
            user_id=data["user_id"],
            program_id=data.get("program_id"),
            items=[ChecklistItem(**x) for x in data["items"]],
            overall_status=data["overall_status"],
            completion_percentage=data["completion_percentage"],
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
