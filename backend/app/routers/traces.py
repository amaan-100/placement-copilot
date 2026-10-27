from fastapi import APIRouter
from sqlalchemy import select

from ..deps import DbSession, SessionId
from ..models import AgentRun
from ..schemas import AgentTraceOut

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("", response_model=list[AgentTraceOut])
def list_traces(db: DbSession, session_id: SessionId) -> list[AgentTraceOut]:
    rows = list(
        db.scalars(
            select(AgentRun)
            .where(AgentRun.session_id == session_id)
            .order_by(AgentRun.id.desc())
            .limit(20)
        )
    )
    return [AgentTraceOut.model_validate(row) for row in rows]
