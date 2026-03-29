"""Unit tests for program / scholarship deadline extraction."""

from datetime import date

from app.services.deadline_extractor import (
    extract_deadlines_from_program,
    extract_deadlines_from_scholarship,
)


def test_extract_program_top_level_deadline():
    program = {
        "program_id": "phd-cs-1",
        "program_name": "PhD CS",
        "application_deadline": "2026-12-01",
    }
    rows = extract_deadlines_from_program(program, "user-a")
    assert len(rows) == 1
    assert rows[0]["deadline_date"] == date(2026, 12, 1)
    assert rows[0]["source_type"] == "program"
    assert rows[0]["source_id"] == "phd-cs-1"
    assert "PhD CS" in rows[0]["item_description"]


def test_extract_program_deadlines_list_dedupes():
    program = {
        "id": "p1",
        "name": "MS Econ",
        "deadlines": [
            {"date": "2026-03-15", "label": "Priority deadline"},
            {"date": "2026-03-15", "label": "Priority deadline"},
        ],
    }
    rows = extract_deadlines_from_program(program, "u1")
    assert len(rows) == 1


def test_extract_scholarship_submission_deadline():
    sch = {
        "scholarship_id": "s99",
        "title": "Merit Award",
        "submission_deadline": "2026-04-20",
    }
    rows = extract_deadlines_from_scholarship(sch, "u2")
    assert len(rows) >= 1
    assert any(r["deadline_date"] == date(2026, 4, 20) for r in rows)
    assert all(r["source_type"] == "scholarship" for r in rows)
    assert all(r["source_id"] == "s99" for r in rows)
