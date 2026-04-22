"""API tests for versioned deadline routes (mock DB via conftest env)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_application_deadlines_v1_empty_with_allow_db_failure(authorization_bearer_header):
    response = client.get(
        "/api/v1/applications/deadlines/any-user-id",
        headers=authorization_bearer_header,
    )
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_post_application_deadlines_sync_v1_reports_extracted(authorization_bearer_header):
    payload = {
        "user_id": "deadline-sync-user",
        "programs": [
            {
                "program_id": "prog-api-1",
                "program_name": "API Program",
                "application_deadline": "2026-11-01",
            }
        ],
        "scholarships": [
            {"scholarship_id": "sch-1", "name": "API Scholarship", "deadline": "2026-09-15"},
        ],
    }
    response = client.post(
        "/api/v1/applications/deadlines/sync",
        json=payload,
        headers=authorization_bearer_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["created_count"] >= 2
    assert data["skipped_duplicates"] == 0
