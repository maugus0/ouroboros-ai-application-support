"""Pure date logic for deadline timeline UI (sorting / status / highlights)."""

from datetime import date
from typing import Literal

TimelineStatus = Literal["completed", "passed", "due_today", "approaching", "upcoming"]


def compute_days_until(deadline: date, today: date) -> int:
    """Calendar days from ``today`` to ``deadline`` (negative if already passed)."""
    return (deadline - today).days


def compute_timeline_fields(
    deadline: date,
    today: date,
    row_status: str,
    approaching_days: int = 30,
    reminder_sent: bool = False,
) -> tuple[TimelineStatus, int, bool, bool, bool]:
    """Return timeline_status, days_until, is_highlighted, reminder_recommended, is_past."""
    days = compute_days_until(deadline, today)
    is_past = days < 0

    if row_status == "completed":
        return ("completed", days, False, False, is_past)
    if row_status == "missed":
        return ("passed", days, False, False, True)
    if is_past:
        return ("passed", days, False, False, True)
    if days == 0:
        highlight = True
        remind = not reminder_sent
        return ("due_today", 0, highlight, remind, False)
    if 1 <= days <= approaching_days:
        return ("approaching", days, True, not reminder_sent, False)
    return ("upcoming", days, False, False, False)
