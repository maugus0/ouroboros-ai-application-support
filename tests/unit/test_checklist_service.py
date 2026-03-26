"""Tests for checklist completion logic."""

from app.services.checklist_service import ChecklistService


def test_compute_status_empty_items():
    overall, pct = ChecklistService.compute_status([])
    assert overall == "not_started"
    assert pct == 0.0


def test_compute_status_all_completed():
    items = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "completed"},
    ]
    overall, pct = ChecklistService.compute_status(items)
    assert overall == "completed"
    assert pct == 100.0


def test_compute_status_in_progress():
    items = [
        {"id": "1", "status": "completed"},
        {"id": "2", "status": "pending"},
    ]
    overall, pct = ChecklistService.compute_status(items)
    assert overall == "in_progress"
    assert pct == 50.0


def test_compute_status_explicit_in_progress():
    items = [
        {"id": "1", "status": "in_progress"},
        {"id": "2", "status": "pending"},
    ]
    overall, pct = ChecklistService.compute_status(items)
    assert overall == "in_progress"
    assert pct == 0.0
