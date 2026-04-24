"""Tests for application configuration."""

# pylint: disable=import-outside-toplevel

import os


def test_settings_load():
    os.environ.setdefault("ALLOW_DB_FAILURE", "true")

    from app.config import settings

    assert settings.DB_NAME == "ouroboros_application_db"
    assert settings.DB_PORT == 3306
    assert settings.DB_POOL_NAME == "application_support_pool"


def test_settings_db_helpers():
    os.environ.setdefault("ALLOW_DB_FAILURE", "true")

    from app.config import settings

    assert isinstance(settings.get_db_host(), str)
    assert isinstance(settings.get_db_port(), int)
    assert isinstance(settings.get_db_name(), str)
    assert isinstance(settings.get_db_user(), str)


def test_sop_settings():
    from app.config import settings

    assert settings.SOP_MIN_WORDS == 500
    assert settings.SOP_MAX_WORDS == 800
    assert 0.0 <= settings.SOP_QUALITY_THRESHOLD <= 1.0


def test_security_settings():
    from app.config import settings

    assert settings.MAX_INPUT_LENGTH > 0
    assert isinstance(settings.ENABLE_PROMPT_INJECTION_DETECTION, bool)
    assert isinstance(settings.ENABLE_OUTPUT_VALIDATION, bool)
    assert settings.INTERNAL_TOKEN_AUDIENCE == "ouroboros.application-support"
    assert isinstance(settings.INTERNAL_TOKEN_VERIFY_ENABLED, bool)


def test_allowed_extensions_list():
    from app.config import settings

    exts = settings.get_allowed_extensions_list()
    assert ".pdf" in exts
    assert ".docx" in exts


def test_allowed_extensions_list_normalizes(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "ALLOWED_EXTENSIONS", " PDF , .DOCX ,, txt ")
    exts = settings.get_allowed_extensions_list()
    assert exts == [".pdf", ".docx", ".txt"]


def test_internal_token_public_keys_rejects_blank_entries(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(
        settings,
        "INTERNAL_TOKEN_PUBLIC_KEYS",
        '{" 0 ":" pem-value ", "blank-kid":"", "blank-pem":"   ", "":"missing-kid"}',
    )

    assert settings.get_internal_token_public_keys() == {"0": "pem-value"}
