from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .db import get_db
from .errors import AppError
from .models import AppSession

DbSession = Annotated[Session, Depends(get_db)]


def get_session_id(request: Request) -> str:
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        raise AppError(500, "session_missing", "Session context is unavailable.")
    return session_id


SessionId = Annotated[str, Depends(get_session_id)]


def get_current_session(db: DbSession, session_id: SessionId) -> AppSession:
    session = db.get(AppSession, session_id)
    if session is None:
        session = AppSession(id=session_id)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


CurrentSession = Annotated[AppSession, Depends(get_current_session)]
