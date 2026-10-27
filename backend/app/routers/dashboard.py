from fastapi import APIRouter
from sqlalchemy import func, select

from ..deps import DbSession, SessionId
from ..models import Application, Interview
from ..schemas import DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def dashboard(db: DbSession, session_id: SessionId) -> DashboardResponse:
    applications = db.scalar(
        select(func.count(Application.id)).where(Application.session_id == session_id)
    )
    pending = db.scalar(
        select(func.count(Application.id)).where(
            Application.session_id == session_id,
            Application.status == "PENDING_APPROVAL",
        )
    )
    approved = db.scalar(
        select(func.count(Application.id)).where(
            Application.session_id == session_id,
            Application.status == "APPROVED",
        )
    )
    interviews = db.scalar(
        select(func.count(Interview.id)).where(Interview.session_id == session_id)
    )
    return DashboardResponse(
        applications=applications or 0,
        pending_approvals=pending or 0,
        approved=approved or 0,
        interviews=interviews or 0,
    )
