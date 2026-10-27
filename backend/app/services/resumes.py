from sqlalchemy import select
from sqlalchemy.orm import Session

from ..errors import AppError
from ..models import Resume


def latest_resume(db: Session, session_id: str) -> Resume | None:
    return db.scalar(
        select(Resume)
        .where(Resume.session_id == session_id)
        .order_by(Resume.id.desc())
        .limit(1)
    )


def latest_resume_or_error(db: Session, session_id: str) -> Resume:
    resume = latest_resume(db, session_id)
    if resume is None:
        raise AppError(400, "resume_required", "Upload a resume first.")
    return resume
