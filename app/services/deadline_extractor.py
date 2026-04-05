"""Extract structured deadline rows from program and scholarship payloads (no LLM)."""

from datetime import date, datetime
from typing import Any


def _parse_date_value(val: Any) -> date | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        chunk = val.strip()[:10]
        if len(chunk) >= 8 and chunk[4] == "-" and chunk[7] == "-":
            try:
                return date.fromisoformat(chunk)
            except ValueError:
                return None
    return None


def _program_display_name(program: dict[str, Any]) -> str:
    return (
        program.get("program_name")
        or program.get("name")
        or program.get("title")
        or program.get("university_name")
        or "Program"
    )


def _scholarship_display_name(scholarship: dict[str, Any]) -> str:
    return scholarship.get("name") or scholarship.get("title") or "Scholarship"


def _append_unique(
    out: list[dict[str, Any]],
    seen: set[tuple[Any, ...]],
    *,
    user_id: str,
    deadline_date: date,
    item_description: str,
    item_category: str,
    source_type: str,
    source_id: str | None,
) -> None:
    desc = (item_description or "")[:500]
    key = (source_type, source_id or "", deadline_date.isoformat(), desc[:200])
    if key in seen:
        return
    seen.add(key)
    out.append(
        {
            "user_id": user_id,
            "checklist_id": None,
            "source_type": source_type,
            "source_id": source_id,
            "deadline_date": deadline_date,
            "deadline_time": None,
            "item_description": desc,
            "item_category": item_category,
            "priority": "high",
        }
    )


def _extend_program_deadlines_from_lists(
    program: dict[str, Any],
    label: str,
    user_id: str,
    source_id_str: str | None,
    out: list[dict[str, Any]],
    seen: set[tuple[Any, ...]],
) -> None:
    for list_key in ("deadlines", "important_dates", "key_dates"):
        arr = program.get(list_key)
        if not isinstance(arr, list):
            continue
        for item in arr:
            if not isinstance(item, dict):
                continue
            d = _parse_date_value(
                item.get("date") or item.get("deadline") or item.get("deadline_date"),
            )
            piece = item.get("name") or item.get("label") or item.get("title") or list_key
            if d is None:
                continue
            _append_unique(
                out,
                seen,
                user_id=user_id,
                deadline_date=d,
                item_description=f"{label}: {piece}",
                item_category="application",
                source_type="program",
                source_id=source_id_str,
            )


def _extend_program_deadlines_from_nested(
    program: dict[str, Any],
    label: str,
    user_id: str,
    source_id_str: str | None,
    out: list[dict[str, Any]],
    seen: set[tuple[Any, ...]],
) -> None:
    nested = program.get("program")
    if not isinstance(nested, dict):
        return
    nested_label = nested.get("name") or nested.get("program_name") or "detail"
    for key in ("application_deadline", "deadline", "deadline_date"):
        d = _parse_date_value(nested.get(key))
        if d is None:
            continue
        _append_unique(
            out,
            seen,
            user_id=user_id,
            deadline_date=d,
            item_description=f"{label} ({nested_label}): {key.replace('_', ' ')}",
            item_category="application",
            source_type="program",
            source_id=source_id_str,
        )


def extract_deadlines_from_program(program: dict[str, Any], user_id: str) -> list[dict[str, Any]]:
    """Pull date fields and optional ``deadlines`` / ``important_dates`` lists from a program dict."""
    source_id = program.get("program_id") or program.get("id")
    source_id_str = str(source_id) if source_id is not None else None
    label = _program_display_name(program)
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def add(d: date | None, desc: str, category: str = "application") -> None:
        if d is None:
            return
        _append_unique(
            out,
            seen,
            user_id=user_id,
            deadline_date=d,
            item_description=desc,
            item_category=category,
            source_type="program",
            source_id=source_id_str,
        )

    for key in ("application_deadline", "deadline", "deadline_date", "application_deadline_date"):
        d = _parse_date_value(program.get(key))
        add(d, f"{label}: {key.replace('_', ' ')}")

    _extend_program_deadlines_from_lists(program, label, user_id, source_id_str, out, seen)
    _extend_program_deadlines_from_nested(program, label, user_id, source_id_str, out, seen)
    return out


def extract_deadlines_from_scholarship(scholarship: dict[str, Any], user_id: str) -> list[dict[str, Any]]:
    """Pull typical scholarship submission / award dates from a scholarship dict."""
    source_id = scholarship.get("scholarship_id") or scholarship.get("id")
    source_id_str = str(source_id) if source_id is not None else None
    label = _scholarship_display_name(scholarship)
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()

    def add(d: date | None, desc: str, category: str = "application") -> None:
        if d is None:
            return
        _append_unique(
            out,
            seen,
            user_id=user_id,
            deadline_date=d,
            item_description=desc,
            item_category=category,
            source_type="scholarship",
            source_id=source_id_str,
        )

    for key in (
        "application_deadline",
        "deadline",
        "deadline_date",
        "submission_deadline",
        "award_notification_date",
    ):
        add(_parse_date_value(scholarship.get(key)), f"{label}: {key.replace('_', ' ')}")

    for list_key in ("deadlines", "important_dates", "milestones"):
        arr = scholarship.get(list_key)
        if not isinstance(arr, list):
            continue
        for item in arr:
            if not isinstance(item, dict):
                continue
            d = _parse_date_value(item.get("date") or item.get("deadline"))
            piece = item.get("name") or item.get("label") or item.get("title") or list_key
            add(d, f"{label}: {piece}")

    return out
