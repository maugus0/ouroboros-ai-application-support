"""FastAPI application entry point for the Application Support Agent."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.api import checklist, cover_letter, deadline, health, sop
from app.config import APP_VERSION, settings
from app.core.logging import get_logger, setup_logging
from app.middleware.logging_middleware import LoggingMiddleware
from app.repositories.db_pool import DatabasePoolConfig, close_pool, create_pool
from app.utils.exceptions import ApplicationSupportBaseError

load_dotenv()


@asynccontextmanager
async def lifespan(_application: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    logger = get_logger("startup")

    logger.info("application_support_agent_starting", version=APP_VERSION)

    if not settings.ALLOW_DB_FAILURE:
        try:
            await create_pool(
                DatabasePoolConfig(
                    host=settings.get_db_host(),
                    port=settings.get_db_port(),
                    db=settings.get_db_name(),
                    user=settings.get_db_user(),
                    password=settings.get_db_password(),
                    pool_size=settings.DB_POOL_SIZE,
                )
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("database_connection_failed", error=str(exc))
            raise
    else:
        logger.warning("database_skipped", reason="ALLOW_DB_FAILURE is True")

    yield

    await close_pool()
    logger.info("application_support_agent_stopped")


app = FastAPI(
    title="Application Support Agent",
    version=APP_VERSION,
    description="Microservice for generating SOPs, cover letters, checklists, and tracking deadlines",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "none",
    },
)

# -- Exception Handlers ------------------------------------------------


@app.exception_handler(ApplicationSupportBaseError)
async def application_support_error_handler(_request: Request, exc: ApplicationSupportBaseError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message},
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_request: Request, exc: RuntimeError):
    return JSONResponse(
        status_code=503,
        content={"success": False, "message": str(exc)},
    )


# -- Middleware ---------------------------------------------------------

app.add_middleware(LoggingMiddleware)

# -- Routers -----------------------------------------------------------

app.include_router(health.router)
app.include_router(sop.router)
app.include_router(cover_letter.router)
app.include_router(checklist.router)
app.include_router(deadline.router)


# -- Custom OpenAPI ----------------------------------------------------


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["info"]["x-logo"] = {"url": "https://ouroboros.ai/logo.png"}
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi  # type: ignore[method-assign]


if __name__ == "__main__":
    import uvicorn

    # Local dev only; Docker/production uses Dockerfile CMD with 0.0.0.0.
    uvicorn.run(app, host="127.0.0.1", port=8005, reload=True)
