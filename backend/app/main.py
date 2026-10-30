import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import engine, run_migrations
from .errors import (
    AppError,
    app_error_handler,
    http_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from .logging_config import configure_logging
from .middleware import (
    RateLimitMiddleware,
    RequestContextMiddleware,
    SessionMiddleware,
)
from .routers import (
    applications,
    dashboard,
    health,
    interviews,
    jobs,
    resumes,
    sessions,
    traces,
)

logger = logging.getLogger("placement")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings.log_level)
    run_migrations()
    logger.info("startup", extra={"environment": settings.environment})
    try:
        yield
    finally:
        engine.dispose()
        logger.info("shutdown")


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Approval-gated multi-agent placement assistant.",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(SessionMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-Id", "X-Request-ID"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

for module in (
    health,
    sessions,
    resumes,
    jobs,
    applications,
    interviews,
    dashboard,
    traces,
):
    app.include_router(module.router)


@app.get("/")
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": app.version,
        "docs": "/docs",
        "health": "/api/health",
    }
