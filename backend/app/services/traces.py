import hashlib
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from ..models import AgentRun, AuditEvent


def text_digest(text: str | None) -> str | None:
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def record_run(
    db: Session,
    session_id: str,
    agent: str,
    action: str,
    output: dict[str, Any],
    latency_ms: int,
    status: str = "ok",
    input_text: str | None = None,
) -> AgentRun:
    run = AgentRun(
        session_id=session_id,
        agent=agent,
        action=action,
        status=status,
        input_digest=text_digest(input_text),
        output=jsonable_encoder(output),
        latency_ms=max(0, int(latency_ms)),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def record_audit(
    db: Session,
    session_id: str,
    action: str,
    application_id: int | None = None,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        session_id=session_id,
        application_id=application_id,
        action=action,
        actor="student",
        details=jsonable_encoder(details or {}),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
