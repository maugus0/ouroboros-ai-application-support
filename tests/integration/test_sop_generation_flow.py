"""End-to-end API tests for SOP generation (mock LLM via USE_MOCK_DATA)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _sample_sop_payload(mock_student_profile, mock_target_program, mock_match_attribution):
    return {
        "user_id": "integration-user",
        "program_id": "prog-1",
        "user_profile": mock_student_profile,
        "target_program": mock_target_program,
        "user_preferences": {"tone": "professional"},
        "match_attribution": mock_match_attribution,
    }


def test_post_sop_generate_returns_success(
    authorization_bearer_header, mock_student_profile, mock_target_program, mock_match_attribution
):
    payload = _sample_sop_payload(mock_student_profile, mock_target_program, mock_match_attribution)
    response = client.post("/sop/generate", json=payload, headers=authorization_bearer_header)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user_id"] == "integration-user"
    assert "content" in body["data"]
    assert body["data"].get("quality_score") is not None
    assert body["data"].get("match_attribution_snapshot", {}).get("overall_score") == 0.87


def test_post_api_v1_applications_generate_sop(
    authorization_bearer_header, mock_student_profile, mock_target_program, mock_match_attribution
):
    payload = _sample_sop_payload(mock_student_profile, mock_target_program, mock_match_attribution)
    response = client.post("/api/v1/applications/generate-sop", json=payload, headers=authorization_bearer_header)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["word_count"] >= 500
    assert body["data"].get("quality_score") is not None


def test_generate_sop_rejects_empty_program_context(authorization_bearer_header):
    response = client.post(
        "/api/v1/applications/generate-sop",
        json={"user_id": "u1", "target_program": {}},
        headers=authorization_bearer_header,
    )
    assert response.status_code == 422


def test_get_sop_not_found(authorization_bearer_header):
    response = client.get("/sop/does-not-exist", headers=authorization_bearer_header)
    # Without a live DB pool (ALLOW_DB_FAILURE=true in CI), repository access raises RuntimeError -> 503.
    assert response.status_code in (404, 503)
