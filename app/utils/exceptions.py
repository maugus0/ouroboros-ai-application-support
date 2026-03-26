"""Custom exception classes for the Application Support Agent."""


class ApplicationSupportBaseError(Exception):
    """Base exception for all Application Support Agent errors."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(ApplicationSupportBaseError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message=message, status_code=500)


class NotFoundError(ApplicationSupportBaseError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str = "Resource"):
        super().__init__(message=f"{resource} not found", status_code=404)


class ValidationError(ApplicationSupportBaseError):
    """Raised when request validation fails beyond Pydantic checks."""

    def __init__(self, message: str = "Validation failed"):
        super().__init__(message=message, status_code=422)


class ServiceAuthError(ApplicationSupportBaseError):
    """Raised when inter-service authentication fails."""

    def __init__(self, message: str = "Service authentication failed"):
        super().__init__(message=message, status_code=401)


class LLMGenerationError(ApplicationSupportBaseError):
    """Raised when LLM generation fails after retries."""

    def __init__(self, message: str = "LLM generation failed"):
        super().__init__(message=message, status_code=502)


class PromptInjectionError(ApplicationSupportBaseError):
    """Raised when prompt injection is detected in user input."""

    def __init__(self, message: str = "Input contains suspicious patterns"):
        super().__init__(message=message, status_code=422)
