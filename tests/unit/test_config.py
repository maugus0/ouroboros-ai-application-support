"""Tests for application configuration."""

import os


def test_settings_load():
    os.environ.setdefault("ALLOW_DB_FAILURE", "true")
    os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")

    from app.config import settings

    assert settings.DB_NAME == "ouroboros_application_db"
    assert settings.DB_PORT == 3306
    assert settings.DB_POOL_NAME == "application_support_pool"


def test_settings_db_helpers():
    os.environ.setdefault("ALLOW_DB_FAILURE", "true")
    os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")

    from app.config import settings

    assert isinstance(settings.get_db_host(), str)
    assert isinstance(settings.get_db_port(), int)
    assert isinstance(settings.get_db_name(), str)
    assert isinstance(settings.get_db_user(), str)


def test_sop_settings():
    os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")
    from app.config import settings

    assert settings.SOP_MIN_WORDS == 500
    assert settings.SOP_MAX_WORDS == 800
    assert 0.0 <= settings.SOP_QUALITY_THRESHOLD <= 1.0


def test_security_settings():
    os.environ.setdefault("X_SERVICE_TOKEN", "test-service-token")
    from app.config import settings

    assert settings.MAX_INPUT_LENGTH > 0
    assert isinstance(settings.ENABLE_PROMPT_INJECTION_DETECTION, bool)
    assert isinstance(settings.ENABLE_OUTPUT_VALIDATION, bool)
