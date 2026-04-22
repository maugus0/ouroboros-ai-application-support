"""Tests for internal bearer token validation."""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def _build_internal_bearer_token(*, audience: str | None = None, issuer: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "test-user",
            "aud": audience or settings.INTERNAL_TOKEN_AUDIENCE,
            "iss": issuer or settings.INTERNAL_TOKEN_ISSUER,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
            "sid": "test-session",
            "trace_id": "test-trace",
            "jti": "test-jti",
        },
        settings.INTERNAL_TOKEN_PUBLIC_KEY,
        algorithm=settings.INTERNAL_TOKEN_SIGNING_ALGORITHM,
        headers={"kid": "internal-v1"},
    )
    return f"Bearer {token}"


def test_missing_internal_bearer_token():
    response = client.post("/sop/generate", json={"user_id": "test"})
    assert response.status_code == 401


def test_invalid_internal_bearer_token():
    response = client.post(
        "/sop/generate",
        json={"user_id": "test"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 401


def test_x_service_token_no_longer_authenticates():
    response = client.post(
        "/sop/generate",
        json={"user_id": "test"},
        headers={"X-Service-Token": "legacy-token"},
    )
    assert response.status_code == 401


def test_internal_bearer_token_rejects_wrong_audience():
    response = client.post(
        "/sop/generate",
        json={"user_id": "test"},
        headers={"Authorization": _build_internal_bearer_token(audience="ouroboros.other-service")},
    )
    assert response.status_code == 401


def test_valid_internal_bearer_token_returns_non_401(authorization_bearer_header):
    response = client.post(
        "/sop/generate",
        json={"user_id": "test"},
        headers=authorization_bearer_header,
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
