"""Thin service layer over ``DeadlineRepository``."""

from datetime import date, datetime, time

from app.config import settings
from app.core.logging import get_logger
from app.models.deadline_models import (
    DeadlineCreateRequest,
    DeadlineResponse,
    DeadlineSyncResponse,
    DeadlineTimelineEntry,
    DeadlineUpdateRequest,
)
from app.repositories.mysql_deadline_repo import DeadlineRepository
from app.services.deadline_extractor import (
    extract_deadlines_from_program,
    extract_deadlines_from_scholarship,
)
from app.utils.db_rows import deadline_row_to_dict
from app.utils.deadline_timeline import compute_timeline_fields
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
            "source_type": request.source_type,
            "source_id": request.source_id,
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
            stored = {
                **row,
                "status": "pending",
                "reminder_sent": False,
                "reminder_sent_at": None,
            }
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

    def _normalize_deadline_date(self, val: date | datetime | object | None) -> date:
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        raise TypeError(f"Expected date, got {type(val)}")

    def _dedupe_key_from_stored(self, row: dict) -> tuple[str, str, str, str]:
        d = deadline_row_to_dict(row)
        dd = self._normalize_deadline_date(d["deadline_date"])
        return (
            d.get("source_type") or "manual",
            (d.get("source_id") or "") or "",
            dd.isoformat(),
            (d.get("item_description") or "")[:200],
        )

    def _dedupe_key_from_extract_row(self, row: dict) -> tuple[str, str, str, str]:
        dd = row["deadline_date"]
        if isinstance(dd, datetime):
            dd = dd.date()
        return (
            row.get("source_type", "manual"),
            (row.get("source_id") or "") or "",
            dd.isoformat(),
            (row.get("item_description") or "")[:200],
        )

    def _timeline_entry(
        self,
        row: dict,
        today: date,
        approaching_days: int,
    ) -> DeadlineTimelineEntry:
        data = deadline_row_to_dict(row)
        dd = self._normalize_deadline_date(data["deadline_date"])
        ts, days, highlighted, remind, past = compute_timeline_fields(
            dd,
            today,
            data["status"],
            approaching_days=approaching_days,
            reminder_sent=data["reminder_sent"],
        )
        base = DeadlineResponse(**{**data, "deadline_date": dd})
        return DeadlineTimelineEntry(
            **base.model_dump(),
            timeline_status=ts,
            days_until_deadline=days,
            is_highlighted=highlighted,
            is_past=past,
            reminder_recommended=remind,
        )

    async def list_timeline_for_user(
        self,
        user_id: str,
        *,
        reference_date: date | None = None,
        approaching_days: int = 30,
    ) -> list[DeadlineTimelineEntry]:
        """All deadlines for user, chronological, with UI timeline fields."""
        if settings.ALLOW_DB_FAILURE:
            return []
        today = reference_date or date.today()
        rows = await self._repo.get_by_user(user_id)
        rows_sorted = sorted(
            rows,
            key=lambda r: (
                self._normalize_deadline_date(r.get("deadline_date")),
                r.get("deadline_time") or time.min,
            ),
        )
        return [self._timeline_entry(row, today, approaching_days) for row in rows_sorted]

    async def sync_from_sources(
        self,
        user_id: str,
        programs: list[dict],
        scholarships: list[dict],
    ) -> DeadlineSyncResponse:
        """Extract deadlines from payloads and insert rows (skip duplicates for same user)."""
        extracted: list[dict] = []
        for prog in programs:
            if isinstance(prog, dict):
                extracted.extend(extract_deadlines_from_program(prog, user_id))
        for sch in scholarships:
            if isinstance(sch, dict):
                extracted.extend(extract_deadlines_from_scholarship(sch, user_id))

        if settings.ALLOW_DB_FAILURE:
            return DeadlineSyncResponse(created_count=len(extracted), skipped_duplicates=0)

        existing = await self._repo.get_by_user(user_id)
        existing_keys = {self._dedupe_key_from_stored(er) for er in existing}
        created = 0
        skipped = 0
        for row in extracted:
            key = self._dedupe_key_from_extract_row(row)
            if key in existing_keys:
                skipped += 1
                continue
            existing_keys.add(key)
            await self._repo.create({**row, "id": generate_uuid()})
            created += 1

        logger.info(
            "deadline_sync_completed",
            user_id=user_id,
            created=created,
            skipped_duplicates=skipped,
        )
        return DeadlineSyncResponse(created_count=created, skipped_duplicates=skipped)
