"""Application configuration loaded from environment variables."""

import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict

APP_VERSION = "0.1.0"


class Settings(BaseSettings):
    """All application settings. Loaded from .env file."""

    # ========== Database ==========
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ouroboros_application_db"
    DB_USERNAME: str = "root"
    DB_PASSWORD: str = ""

    DB_POOL_SIZE: int = 10
    DB_POOL_NAME: str = "application_support_pool"
    DB_CONNECTION_TIMEOUT: int = 20

    # ========== Inter-Service Auth ==========
    INTERNAL_TOKEN_VERIFY_ENABLED: bool = False
    INTERNAL_TOKEN_SIGNING_ALGORITHM: str = "RS256"
    INTERNAL_TOKEN_PUBLIC_KEY: str = ""
    INTERNAL_TOKEN_PUBLIC_KEYS: str = "{}"
    INTERNAL_TOKEN_JWKS_URL: str = ""
    INTERNAL_TOKEN_JWKS_REFRESH_SECONDS: int = 60
    INTERNAL_TOKEN_JWKS_TIMEOUT_SECONDS: int = 2
    INTERNAL_TOKEN_AUDIENCE: str = "ouroboros.application-support"
    INTERNAL_TOKEN_ISSUER: str = "ouroboros-orchestrator-internal"

    # ========== LLM Configuration ==========
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 2000
    OPENAI_TEMPERATURE: float = 0.2

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    ANTHROPIC_MAX_TOKENS: int = 2000

    LLM_MAX_RETRIES: int = 3
    LLM_RETRY_DELAY: int = 2

    # ========== SOP Generation ==========
    SOP_MIN_WORDS: int = 500
    SOP_MAX_WORDS: int = 800
    SOP_QUALITY_THRESHOLD: float = 0.7

    # ========== Document Generation ==========
    DOCX_TEMPLATE_DIR: str = "templates/docx"
    OUTPUT_DIR: str = "/tmp/outputs"

    # ========== File uploads (DOCX export / future uploads) ==========
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = ".pdf,.docx,.doc,.jpg,.jpeg,.png"
    TEMP_UPLOAD_DIR: str = "/tmp/uploads"

    # ========== Retrieval (Style Reference) ==========
    RETRIEVAL_TOP_K: int = 2
    RETRIEVAL_ENABLED: bool = True

    # ========== Security ==========
    MAX_INPUT_LENGTH: int = 10000
    ENABLE_PROMPT_INJECTION_DETECTION: bool = True
    ENABLE_OUTPUT_VALIDATION: bool = True

    # ========== Application ==========
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    USE_MOCK_DATA: bool = False
    ALLOW_DB_FAILURE: bool = False

    # ========== Docker ==========
    RUN_STARTUP_SCRIPTS: bool = True
    DOCKER_MYSQL_PORT: int = 3308

    # ========== Deadline reminders (optional APScheduler in lifespan) ==========
    DEADLINE_REMINDER_SCHEDULER_ENABLED: bool = False
    DEADLINE_REMINDER_INTERVAL_MINUTES: int = 360

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    def get_db_host(self) -> str:
        return os.getenv("MYSQL_HOST", self.DB_HOST)

    def get_db_name(self) -> str:
        return os.getenv("MYSQL_DATABASE", self.DB_NAME)

    def get_db_user(self) -> str:
        return os.getenv("MYSQL_USER", self.DB_USERNAME)

    def get_db_password(self) -> str:
        return os.getenv("MYSQL_PASSWORD", self.DB_PASSWORD)

    def get_db_port(self) -> int:
        val = os.getenv("MYSQL_PORT")
        return int(val) if val is not None else self.DB_PORT

    def get_allowed_extensions_list(self) -> list[str]:
        """Return allowed extensions: trimmed, lowercased, dotted, empty segments skipped."""
        extensions: list[str] = []
        for raw in self.ALLOWED_EXTENSIONS.split(","):
            ext = raw.strip().lower()
            if not ext:
                continue
            if not ext.startswith("."):
                ext = f".{ext}"
            extensions.append(ext)
        return extensions

    def get_internal_token_public_keys(self) -> dict[str, str]:
        """Parse INTERNAL_TOKEN_PUBLIC_KEYS JSON string into a kid->PEM dict."""
        try:
            parsed = json.loads(self.INTERNAL_TOKEN_PUBLIC_KEYS)
        except (TypeError, json.JSONDecodeError):
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(kid): str(pem) for kid, pem in parsed.items() if kid and pem}


settings = Settings()
