import logging

from fastapi import APIRouter

from ..db import check_db
from ..errors import AppError
from ..providers.llm import status as llm_status
from ..schemas import HealthResponse, LlmStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        agent="Placement Co-pilot",
        approval_gate=True,
    )


@router.get("/api/llm/status", response_model=LlmStatusResponse)
async def llm_status_endpoint() -> LlmStatusResponse:
    details = await llm_status()
    return LlmStatusResponse(
        enabled=bool(details.get("enabled")),
        available=bool(details.get("model_available")),
    )


@router.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@router.get("/readyz")
def readyz() -> dict:
    try:
        check_db()
    except Exception:
        logger.exception("readiness_check_failed")
        raise AppError(503, "database_unavailable", "Database is not ready.") from None
    return {"status": "ready", "database": "ok"}
