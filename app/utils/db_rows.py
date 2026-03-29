"""Helpers for mapping MySQL rows to API models."""

import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.utils.exceptions import ValidationError


def _parse_json_field(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _decimal_to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def checklist_items_from_row(items: Any) -> list[dict[str, Any]]:
    """Normalise checklist ``items`` JSON from MySQL to a list of dicts."""
    parsed = _parse_json_field(items)
    if isinstance(parsed, list):
        return parsed
    return []


def checklist_items_for_update(items_raw: Any) -> list[dict[str, Any]]:
    """Parse checklist ``items`` from a row for in-place updates; strict JSON for string blobs."""
    if isinstance(items_raw, list):
        return list(items_raw)
    if isinstance(items_raw, str):
        if not items_raw.strip():
            return []
        try:
            parsed = json.loads(items_raw)
        except json.JSONDecodeError as exc:
            raise ValidationError("Checklist items contain invalid JSON") from exc
        if not isinstance(parsed, list):
            raise ValidationError("Checklist items must be a JSON array")
        return list(parsed)
    return []


def sop_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise a ``generated_sops`` row for ``SOPResponse`` construction."""
    qf = _parse_json_field(row.get("quality_feedback"))
    feedback: list[str] | None = None
    if isinstance(qf, list):
        feedback = [str(x) for x in qf]
    elif isinstance(qf, dict):
        feedback = [str(v) for v in qf.values()]
    created = row.get("created_at")
    updated = row.get("updated_at")
    qs = row.get("quality_score")
    if qs is not None:
        qs = _decimal_to_float(qs)
    attr = _parse_json_field(row.get("match_attribution_snapshot"))
    attr_dict: dict[str, Any] | None = None
    if isinstance(attr, dict):
        attr_dict = attr

    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "program_id": row.get("program_id"),
        "version": int(row.get("version") or 1),
        "content": row["content"],
        "word_count": int(row.get("word_count") or 0),
        "quality_score": qs,
        "quality_feedback": feedback,
        "match_attribution_snapshot": attr_dict,
        "llm_model_used": row.get("llm_model_used"),
        "llm_fallback_used": bool(row.get("llm_fallback_used")),
        "total_processing_time_ms": (
            int(row["total_processing_time_ms"]) if row.get("total_processing_time_ms") is not None else None
        ),
        "created_at": created if isinstance(created, datetime) else None,
        "updated_at": updated if isinstance(updated, datetime) else None,
    }


def cover_letter_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise a ``generated_cover_letters`` row for ``CoverLetterResponse``."""
    created = row.get("created_at")
    updated = row.get("updated_at")
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "target_type": row["target_type"],
        "target_id": row.get("target_id"),
        "version": int(row.get("version") or 1),
        "content": row["content"],
        "word_count": int(row.get("word_count") or 0),
        "llm_model_used": row.get("llm_model_used"),
        "llm_fallback_used": bool(row.get("llm_fallback_used")),
        "total_processing_time_ms": (
            int(row["total_processing_time_ms"]) if row.get("total_processing_time_ms") is not None else None
        ),
        "created_at": created if isinstance(created, datetime) else None,
        "updated_at": updated if isinstance(updated, datetime) else None,
    }


def checklist_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise an ``application_checklists`` row for ``ChecklistResponse``."""
    items = checklist_items_from_row(row.get("items"))
    pct = row.get("completion_percentage")
    if isinstance(pct, Decimal):
        pct = float(pct)
    created = row.get("created_at")
    updated = row.get("updated_at")
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "program_id": row.get("program_id"),
        "items": items,
        "overall_status": row.get("overall_status") or "not_started",
        "completion_percentage": float(pct or 0.0),
        "created_at": created if isinstance(created, datetime) else None,
        "updated_at": updated if isinstance(updated, datetime) else None,
    }


def deadline_row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    """Normalise a ``deadline_entries`` row for ``DeadlineResponse``."""
    dd = row.get("deadline_date")
    if isinstance(dd, datetime):
        dd = dd.date()
    dt = row.get("deadline_time")
    rsa = row.get("reminder_sent_at")
    created = row.get("created_at")
    updated = row.get("updated_at")
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "checklist_id": row.get("checklist_id"),
        "deadline_date": dd,
        "deadline_time": dt,
        "item_description": row["item_description"],
        "item_category": row.get("item_category") or "application",
        "priority": row.get("priority") or "medium",
        "status": row.get("status") or "pending",
        "reminder_sent": bool(row.get("reminder_sent")),
        "reminder_sent_at": rsa if isinstance(rsa, datetime) else None,
        "created_at": created if isinstance(created, datetime) else None,
        "updated_at": updated if isinstance(updated, datetime) else None,
    }
