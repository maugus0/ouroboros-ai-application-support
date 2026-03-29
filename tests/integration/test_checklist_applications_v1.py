"""API tests for versioned application checklist routes (mock DB via conftest env)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_application_checklist_v1_generates_items(service_token_header):
    payload = {
        "user_id": "checklist-int-user",
        "program_id": "prog-int-1",
        "program_requirements": "All applicants must submit official GRE and TOEFL scores.",
    }
    response = client.post(
        "/api/v1/applications/checklist",
        json=payload,
        headers=service_token_header,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["user_id"] == "checklist-int-user"
    assert len(data["items"]) >= 6
    joined = " ".join(i["description"].lower() for i in data["items"])
    assert "transcript" in joined
    assert "gre" in joined
    assert "toefl" in joined or "english proficiency" in joined
    assert data["completion_percentage"] == 0.0


def test_get_application_checklists_v1_returns_200(service_token_header):
    # With ALLOW_DB_FAILURE=true, list is empty (no persistence); still validates route + auth.
    response = client.get(
        "/api/v1/applications/checklist/any-user-id",
        headers=service_token_header,
    )
    assert response.status_code == 200
    assert response.json()["data"] == []
