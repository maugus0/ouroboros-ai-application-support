"""Focused tests for application-support internal bearer auth."""

import json
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from app.main import app

INTERNAL_TEST_KEY = "internal-test-signing-key-with-32-bytes"

client = TestClient(app)


def _generate_rsa_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem


def _build_hs256_token(
    *,
    audience: str = "ouroboros.application-support",
    issuer: str = "ouroboros-orchestrator-internal",
    expires_delta_seconds: int = 120,
) -> str:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": audience,
            "iss": issuer,
            "iat": now,
            "exp": now + timedelta(seconds=expires_delta_seconds),
            "trace_id": "trace-1",
            "jti": "jti-1",
        },
        INTERNAL_TEST_KEY,
        algorithm="HS256",
        headers={"kid": "internal-v1"},
    )
    return f"Bearer {token}"


def _build_rs256_token(
    private_key: str,
    *,
    kid: str = "internal-v1",
    audience: str = "ouroboros.application-support",
) -> str:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "user-123",
            "aud": audience,
            "iss": "ouroboros-orchestrator-internal",
            "iat": now,
            "exp": now + timedelta(seconds=120),
            "trace_id": "trace-1",
            "jti": "jti-1",
        },
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )
    return f"Bearer {token}"


def _configure_hs256(monkeypatch):
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_VERIFY_ENABLED", True)
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_SIGNING_ALGORITHM", "HS256")
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_PUBLIC_KEY", INTERNAL_TEST_KEY)
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_AUDIENCE", "ouroboros.application-support")
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_ISSUER", "ouroboros-orchestrator-internal")


def test_valid_internal_bearer_token_is_accepted(monkeypatch):
    _configure_hs256(monkeypatch)

    response = client.get(
        "/api/v1/applications/deadlines/user-123",
        headers={"Authorization": _build_hs256_token(), "X-User-ID": "user-123"},
    )

    assert response.status_code not in (401, 403)


def test_internal_bearer_token_rejects_wrong_issuer(monkeypatch):
    _configure_hs256(monkeypatch)

    response = client.get(
        "/api/v1/applications/deadlines/user-123",
        headers={"Authorization": _build_hs256_token(issuer="unexpected-issuer")},
    )

    assert response.status_code == 401


def test_internal_bearer_token_rejects_expired_token(monkeypatch):
    _configure_hs256(monkeypatch)

    response = client.get(
        "/api/v1/applications/deadlines/user-123",
        headers={"Authorization": _build_hs256_token(expires_delta_seconds=-60)},
    )

    assert response.status_code == 401


def test_internal_bearer_token_uses_configured_public_keys_by_kid(monkeypatch):
    private_pem, public_pem = _generate_rsa_keypair()

    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_VERIFY_ENABLED", True)
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_SIGNING_ALGORITHM", "RS256")
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_PUBLIC_KEY", "")
    monkeypatch.setattr(
        "app.middleware.service_auth.settings.INTERNAL_TOKEN_PUBLIC_KEYS",
        json.dumps({"internal-config-kid": public_pem.replace("\n", "\\n")}),
    )
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_JWKS_URL", "")
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_AUDIENCE", "ouroboros.application-support")
    monkeypatch.setattr("app.middleware.service_auth.settings.INTERNAL_TOKEN_ISSUER", "ouroboros-orchestrator-internal")

    response = client.get(
        "/api/v1/applications/deadlines/user-123",
        headers={
            "Authorization": _build_rs256_token(private_pem, kid="internal-config-kid"),
            "X-User-ID": "user-123",
        },
    )

    assert response.status_code not in (401, 403)
