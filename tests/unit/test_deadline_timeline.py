"""Unit tests for deadline timeline classification (no DB)."""

from datetime import date

from app.utils.deadline_timeline import compute_days_until, compute_timeline_fields


def test_compute_days_until_negative_when_past():
    assert compute_days_until(date(2026, 1, 1), date(2026, 1, 10)) == -9


def test_compute_timeline_passed_for_old_pending():
    ts, days, hi, _rr, past = compute_timeline_fields(
        date(2026, 1, 1),
        date(2026, 6, 1),
        "pending",
        approaching_days=30,
        reminder_sent=False,
    )
    assert ts == "passed"
    assert past is True
    assert hi is False
    assert days < 0


def test_compute_timeline_approaching_highlight_and_reminder():
    ts, days, hi, rr, past = compute_timeline_fields(
        date(2026, 6, 20),
        date(2026, 6, 1),
        "pending",
        approaching_days=30,
        reminder_sent=False,
    )
    assert ts == "approaching"
    assert days == 19
    assert hi is True
    assert rr is True
    assert past is False


def test_compute_timeline_due_today():
    ts, days, hi, rr, _past = compute_timeline_fields(
        date(2026, 6, 1),
        date(2026, 6, 1),
        "pending",
        approaching_days=30,
        reminder_sent=False,
    )
    assert ts == "due_today"
    assert days == 0
    assert hi is True
    assert rr is True


def test_compute_timeline_no_reminder_if_already_sent():
    _ts, _d, _hi, rr, _p = compute_timeline_fields(
        date(2026, 6, 10),
        date(2026, 6, 1),
        "pending",
        approaching_days=30,
        reminder_sent=True,
    )
    assert rr is False


def test_compute_timeline_outside_approaching_window_is_upcoming():
    ts, _d, _hi, _rr, _p = compute_timeline_fields(
        date(2026, 8, 1),
        date(2026, 6, 1),
        "pending",
        approaching_days=30,
        reminder_sent=False,
    )
    assert ts == "upcoming"
