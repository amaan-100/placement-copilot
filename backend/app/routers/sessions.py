from fastapi import APIRouter

from ..deps import CurrentSession
from ..schemas import SessionResponse

router = APIRouter(prefix="/api/session", tags=["sessions"])


@router.get("", response_model=SessionResponse)
def get_session(session: CurrentSession) -> SessionResponse:
    return SessionResponse(session_id=session.id, created_at=session.created_at)
