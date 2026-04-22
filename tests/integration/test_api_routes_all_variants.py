"""Integration coverage for every HTTP route variant (CI: ALLOW_DB_FAILURE + USE_MOCK_DATA).

Exercises legacy paths vs ``/api/v1/applications/*``, query params, and expected status when DB is skipped.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# -- Public (no service token) -------------------------------------------------


def test_get_root_returns_healthy():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "healthy"
    assert "version" in body


def test_get_health_returns_healthy():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "healthy"


# -- SOP: legacy + v1 + validation + read + versions ----------------------------


def test_post_sop_generate_legacy(
    authorization_bearer_header, mock_student_profile, mock_target_program, mock_match_attribution
):
    payload = {
        "user_id": "sop-legacy-variant",
        "program_id": "prog-sl",
        "user_profile": mock_student_profile,
        "target_program": mock_target_program,
        "match_attribution": mock_match_attribution,
    }
    r = client.post("/sop/generate", json=payload, headers=authorization_bearer_header)
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["user_id"] == "sop-legacy-variant"
    assert d.get("content")


def test_post_sop_generate_v1_same_shape(
    authorization_bearer_header, mock_student_profile, mock_target_program, mock_match_attribution
):
    payload = {
        "user_id": "sop-v1-variant",
        "program_id": "prog-sv1",
        "user_profile": mock_student_profile,
        "target_program": mock_target_program,
        "match_attribution": mock_match_attribution,
    }
    r = client.post("/api/v1/applications/generate-sop", json=payload, headers=authorization_bearer_header)
    assert r.status_code == 200
    assert r.json()["data"].get("word_count", 0) >= 500


def test_get_sop_by_id_not_found_or_no_db(authorization_bearer_header):
    rid = str(uuid.uuid4())
    r = client.get(f"/sop/{rid}", headers=authorization_bearer_header)
    assert r.status_code in (404, 503)


def test_get_sop_versions_not_found_or_no_db(authorization_bearer_header):
    rid = str(uuid.uuid4())
    r = client.get(f"/sop/versions/{rid}", headers=authorization_bearer_header)
    assert r.status_code in (404, 503)


# -- Checklist: v1 + legacy + explicit items + PUT not found -------------------


def test_post_checklist_v1_with_explicit_items(authorization_bearer_header):
    r = client.post(
        "/api/v1/applications/checklist",
        json={
            "user_id": "chk-v1-explicit",
            "program_id": "p1",
            "items": [
                {"description": "Custom task A", "status": "pending", "category": "documents", "priority": "high"},
                {"description": "Custom task B", "status": "in_progress", "category": "general", "priority": "low"},
            ],
        },
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data["items"]) == 2
    assert data["overall_status"] == "in_progress"


def test_post_checklist_legacy_create(authorization_bearer_header):
    r = client.post(
        "/checklists",
        json={
            "user_id": "chk-legacy-user",
            "program_id": "p-leg",
            "program_requirements": "TOEFL required.",
        },
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200
    assert len(r.json()["data"]["items"]) >= 6


def test_get_checklist_legacy_empty_without_db(authorization_bearer_header):
    r = client.get("/checklists/nonexistent-checklist-user-xyz", headers=authorization_bearer_header)
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_put_checklist_v1_item_not_found_without_db(authorization_bearer_header):
    r = client.put(
        f"/api/v1/applications/checklist/{uuid.uuid4()}/item/{uuid.uuid4()}",
        json={"status": "completed"},
        headers=authorization_bearer_header,
    )
    assert r.status_code == 404


def test_put_checklist_legacy_item_not_found_without_db(authorization_bearer_header):
    r = client.put(
        f"/checklists/{uuid.uuid4()}/items/{uuid.uuid4()}",
        json={"status": "completed"},
        headers=authorization_bearer_header,
    )
    assert r.status_code == 404


# -- Deadlines: v1 timeline + sync variants + legacy CRUD ----------------------


def test_get_deadlines_v1_default_approaching_window(authorization_bearer_header):
    r = client.get("/api/v1/applications/deadlines/some-user", headers=authorization_bearer_header)
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_get_deadlines_v1_custom_approaching_days(authorization_bearer_header):
    r = client.get(
        "/api/v1/applications/deadlines/some-user?approaching_days=7",
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200


def test_get_deadlines_v1_approaching_days_max_boundary(authorization_bearer_header):
    r = client.get(
        "/api/v1/applications/deadlines/some-user?approaching_days=366",
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200


def test_get_deadlines_v1_invalid_approaching_days_422(authorization_bearer_header):
    r = client.get(
        "/api/v1/applications/deadlines/some-user?approaching_days=0",
        headers=authorization_bearer_header,
    )
    assert r.status_code == 422


def test_post_deadlines_sync_empty_sources(authorization_bearer_header):
    r = client.post(
        "/api/v1/applications/deadlines/sync",
        json={"user_id": "sync-empty", "programs": [], "scholarships": []},
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["created_count"] == 0
    assert data["skipped_duplicates"] == 0


def test_post_deadlines_sync_program_nested_and_lists(authorization_bearer_header):
    r = client.post(
        "/api/v1/applications/deadlines/sync",
        json={
            "user_id": "sync-rich",
            "programs": [
                {
                    "program_id": "nested-prog",
                    "program_name": "Nested U",
                    "deadline_date": "2026-05-01",
                    "deadlines": [{"date": "2026-06-01", "label": "Round 2"}],
                    "program": {"application_deadline": "2026-04-01"},
                }
            ],
            "scholarships": [
                {
                    "id": "sch-mile",
                    "name": "Milestone Fund",
                    "milestones": [{"date": "2026-07-01", "title": "Final"}],
                }
            ],
        },
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200
    assert r.json()["data"]["created_count"] >= 1


def test_post_legacy_deadline_create(authorization_bearer_header):
    r = client.post(
        "/deadlines",
        json={
            "user_id": "dl-legacy-u1",
            "deadline_date": "2027-03-01",
            "item_description": "Legacy create variant",
            "item_category": "document",
            "priority": "high",
            "source_type": "manual",
        },
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["data"]["user_id"] == "dl-legacy-u1"
    assert body["data"]["item_category"] == "document"


def test_get_legacy_deadlines_list_empty_without_db(authorization_bearer_header):
    r = client.get("/deadlines/no-deadlines-user-abc", headers=authorization_bearer_header)
    assert r.status_code == 200
    assert r.json()["data"] == []


def test_put_legacy_deadline_not_found_without_db(authorization_bearer_header):
    r = client.put(
        f"/deadlines/{uuid.uuid4()}",
        json={"status": "completed"},
        headers=authorization_bearer_header,
    )
    assert r.status_code == 404


# -- Cover letters: generate + get + target_type variants -----------------------


def _cover_letter_payload(user_id: str, target_type: str):
    return {
        "user_id": user_id,
        "target_type": target_type,
        "target_id": "t-1",
        "user_profile": {"full_name": "Variant User"},
        "target_details": {"note": "integration"},
    }


@pytest.mark.parametrize(
    "target_type",
    ["program", "scholarship", "professor", "other"],
)
def test_post_cover_letter_generate_each_target_type(authorization_bearer_header, target_type):
    r = client.post(
        "/cover-letters/generate",
        json=_cover_letter_payload(f"cl-{target_type}", target_type),
        headers=authorization_bearer_header,
    )
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["target_type"] == target_type
    assert d.get("content")


def test_get_cover_letter_not_found_or_no_db(authorization_bearer_header):
    r = client.get(f"/cover-letters/{uuid.uuid4()}", headers=authorization_bearer_header)
    assert r.status_code in (404, 503)


# -- Auth on new v1 routes ----------------------------------------------------


def test_deadlines_sync_without_token_401():
    r = client.post("/api/v1/applications/deadlines/sync", json={"user_id": "x"})
    assert r.status_code == 401
