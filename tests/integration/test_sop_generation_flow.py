"""End-to-end API tests for SOP generation (mock LLM via USE_MOCK_DATA)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_sop_generate_returns_success(service_token_header):
    payload = {
        "user_id": "integration-user",
        "program_id": "prog-1",
        "user_profile": {"full_name": "Test Student"},
        "target_program": {"field_of_study": "Computer Science"},
        "user_preferences": {},
    }
    response = client.post("/sop/generate", json=payload, headers=service_token_header)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user_id"] == "integration-user"
    assert "content" in body["data"]


def test_get_sop_not_found(service_token_header):
    response = client.get("/sop/does-not-exist", headers=service_token_header)
    # Without a live DB pool (ALLOW_DB_FAILURE=true in CI), repository access raises RuntimeError -> 503.
    assert response.status_code in (404, 503)
