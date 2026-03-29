"""Tests for standard checklist templates and program-requirement extraction."""

from app.services.checklist_item_builder import (
    build_default_checklist_items,
    extract_program_specific_items,
    standard_checklist_items,
)


def test_standard_items_include_core_documents():
    std = standard_checklist_items()
    blob = " ".join(i["description"].lower() for i in std)
    assert "cv" in blob or "resume" in blob
    assert "transcript" in blob
    assert "recommendation" in blob
    assert "statement" in blob


def test_extract_gre_toefl_from_text():
    text = "Applicants must submit GRE General scores and TOEFL iBT."
    extra = extract_program_specific_items(text)
    desc = " ".join(x["description"].lower() for x in extra)
    assert "gre" in desc
    assert "toefl" in desc or "english proficiency" in desc


def test_build_default_merges_hints_without_duplicate_gre():
    items = build_default_checklist_items(
        "GRE required for all applicants.",
        {"requires_gre": True},
    )
    gre_rows = [i for i in items if "gre" in i["description"].lower()]
    assert len(gre_rows) == 1


def test_empty_requirements_yields_only_standard():
    items = build_default_checklist_items(None, {})
    assert len(items) == len(standard_checklist_items())
