"""Pytest configuration and shared fixtures."""

import os

import pytest

os.environ.setdefault("ALLOW_DB_FAILURE", "true")
os.environ.setdefault("USE_MOCK_DATA", "true")
os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")

from app.config import settings  # noqa: E402  # pylint: disable=wrong-import-position


@pytest.fixture
def mock_settings():
    return {
        "DB_HOST": "localhost",
        "DB_NAME": "test_db",
        "USE_MOCK_DATA": True,
        "ALLOW_DB_FAILURE": True,
        "X_SERVICE_TOKEN": settings.X_SERVICE_TOKEN,
    }


@pytest.fixture
def service_token_header():
    """Header value always matches ``settings.X_SERVICE_TOKEN`` (local + CI)."""
    return {"X-Service-Token": settings.X_SERVICE_TOKEN}


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
