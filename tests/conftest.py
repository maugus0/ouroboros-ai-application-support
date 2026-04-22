"""Pytest configuration and shared fixtures."""

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest

os.environ.setdefault("ALLOW_DB_FAILURE", "true")
os.environ.setdefault("USE_MOCK_DATA", "true")
os.environ.setdefault("INTERNAL_TOKEN_VERIFY_ENABLED", "true")
os.environ.setdefault("INTERNAL_TOKEN_SIGNING_ALGORITHM", "HS256")
os.environ.setdefault("INTERNAL_TOKEN_PUBLIC_KEY", "internal-test-signing-key-with-32-bytes")
os.environ.setdefault("INTERNAL_TOKEN_ISSUER", "ouroboros-orchestrator-internal")
os.environ.setdefault("INTERNAL_TOKEN_AUDIENCE", "ouroboros.application-support")

from app.config import settings  # noqa: E402  # pylint: disable=wrong-import-position


@pytest.fixture
def mock_settings():
    return {
        "DB_HOST": "localhost",
        "DB_NAME": "test_db",
        "USE_MOCK_DATA": True,
        "ALLOW_DB_FAILURE": True,
        "INTERNAL_TOKEN_VERIFY_ENABLED": True,
    }


@pytest.fixture
def authorization_bearer_header():
    """Return an orchestrator-style internal bearer token for tests."""
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": "test-user",
            "aud": settings.INTERNAL_TOKEN_AUDIENCE,
            "iss": settings.INTERNAL_TOKEN_ISSUER,
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
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_student_profile():
    """Rich student profile for SOP generation tests."""
    return {
        "full_name": "Alex Rivera",
        "education": [
            {"degree": "BS", "major": "Computer Science", "institution": "State University", "gpa": "3.7"},
        ],
        "experience": [{"role": "Research assistant", "lab": "ML Systems", "years": "2"}],
        "research_interests": ["efficient inference", "systems for ML"],
    }


@pytest.fixture
def mock_target_program():
    """Target graduate program context."""
    return {
        "field_of_study": "Computer Science",
        "degree_level": "PhD",
        "university_name": "Example University",
        "program_name": "PhD in Computer Science",
    }


@pytest.fixture
def mock_match_attribution():
    """Sample eligibility / fit payload stored as snapshot on generated SOPs."""
    return {"overall_score": 0.87, "summary": "Strong research fit", "dimensions": {"research_fit": 0.9}}
