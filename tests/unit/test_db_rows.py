"""Tests for DB row normalisation helpers."""

from app.utils.db_rows import checklist_items_from_row, sop_row_to_dict


def test_checklist_items_from_row_list():
    raw = [{"id": "1", "description": "a", "status": "pending"}]
    assert checklist_items_from_row(raw) == raw


def test_sop_row_to_dict_quality_feedback_json_string():
    row = {
        "id": "s1",
        "user_id": "u1",
        "program_id": None,
        "version": 1,
        "content": "hello world",
        "word_count": 2,
        "quality_score": None,
        "quality_feedback": '["a", "b"]',
        "llm_model_used": "m",
        "llm_fallback_used": 0,
        "total_processing_time_ms": 10,
        "created_at": None,
        "updated_at": None,
    }
    d = sop_row_to_dict(row)
    assert d["quality_feedback"] == ["a", "b"]


def test_sop_row_to_dict_match_attribution_snapshot():
    row = {
        "id": "s1",
        "user_id": "u1",
        "program_id": "p1",
        "version": 1,
        "content": "x",
        "word_count": 1,
        "quality_score": None,
        "quality_feedback": None,
        "llm_model_used": None,
        "llm_fallback_used": 0,
        "total_processing_time_ms": None,
        "created_at": None,
        "updated_at": None,
        "match_attribution_snapshot": '{"overall_score": 0.9}',
    }
    d = sop_row_to_dict(row)
    assert d["match_attribution_snapshot"] == {"overall_score": 0.9}
