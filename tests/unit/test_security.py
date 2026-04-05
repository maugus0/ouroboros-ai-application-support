"""Tests for X-Service-Token validation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_service_token():
    response = client.post("/sop/generate", json={"user_id": "test"})
    assert response.status_code == 401


def test_invalid_service_token():
    response = client.post(
        "/sop/generate",
        json={"user_id": "test"},
        headers={"X-Service-Token": "wrong-token"},
    )
    assert response.status_code == 403


def test_valid_service_token_returns_non_401(service_token_header):
    response = client.post(
        "/sop/generate",
        json={"user_id": "test"},
        headers=service_token_header,
    )
    assert response.status_code not in (401, 403)


def test_missing_token_on_deadlines():
    response = client.get("/deadlines/user-123")
    assert response.status_code == 401


def test_missing_token_on_applications_deadlines_v1():
    response = client.get("/api/v1/applications/deadlines/user-123")
    assert response.status_code == 401


def test_missing_token_on_checklists():
    response = client.get("/checklists/user-123")
    assert response.status_code == 401


def test_missing_token_on_cover_letters():
    response = client.post("/cover-letters/generate", json={"user_id": "test"})
    assert response.status_code == 401
