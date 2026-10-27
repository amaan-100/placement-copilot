import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .db import SessionLocal
from .logging_config import request_id_var
from .models import AppSession, utcnow

logger = logging.getLogger(__name__)

HEALTH_PATHS = {"/api/health", "/healthz", "/readyz"}


def normalize_session_id(raw: str | None) -> str | None:
    if not raw:
        return None
    try:
        return str(uuid.UUID(raw.strip()))
    except (ValueError, AttributeError):
        return None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration,
                },
            )
            request_id_var.reset(token)
            raise

        duration = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        if request.url.path not in HEALTH_PATHS:
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration,
                },
            )
        request_id_var.reset(token)
        return response


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header_id = normalize_session_id(request.headers.get(settings.session_header_name))
        cookie_id = normalize_session_id(request.cookies.get(settings.session_cookie_name))
        session_id = header_id or cookie_id or str(uuid.uuid4())
        request.state.session_id = session_id

        try:
            with SessionLocal() as db:
                session = db.get(AppSession, session_id)
                if session is None:
                    db.add(AppSession(id=session_id))
                else:
                    session.last_seen_at = utcnow()
                db.commit()
        except SQLAlchemyError:
            logger.exception("session_upsert_failed", extra={"session_id": session_id})

        response = await call_next(request)
        response.headers[settings.session_header_name] = session_id
        response.set_cookie(
            settings.session_cookie_name,
            session_id,
            max_age=settings.session_max_age_seconds,
            httponly=True,
            samesite="lax",
            secure=settings.is_production,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _limit_for(self, path: str) -> tuple[int, str]:
        if path == "/api/resume/upload":
            return settings.rate_limit_upload_requests, "upload"
        return settings.rate_limit_requests, "api"

    def _check(self, key: tuple[str, str], limit: int, window: int) -> float | None:
        now = time.monotonic()
        cutoff = now - window
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] < cutoff:
                hits.popleft()
            if len(hits) >= limit:
                return max(1.0, window - (now - hits[0]))
            hits.append(now)
            if len(self._hits) > 10_000:
                self._hits.clear()
        return None

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/") or path in HEALTH_PATHS:
            return await call_next(request)

        identity = getattr(request.state, "session_id", None) or (
            request.client.host if request.client else "anonymous"
        )
        limit, bucket = self._limit_for(path)
        retry_after = self._check(
            (identity, bucket),
            limit,
            settings.rate_limit_window_seconds,
        )
        if retry_after is not None:
            request_id = getattr(request.state, "request_id", None)
            body: dict = {
                "error": {
                    "code": "rate_limited",
                    "message": "Too many requests. Please wait and try again.",
                }
            }
            if request_id:
                body["request_id"] = request_id
            return JSONResponse(
                status_code=429,
                content=body,
                headers={"Retry-After": str(int(retry_after))},
            )
        return await call_next(request)
