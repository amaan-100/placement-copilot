import time

from fastapi import APIRouter
from sqlalchemy import select

from ..agents import orchestrator
from ..deps import DbSession, SessionId
from ..errors import AppError
from ..models import Application, Job, utcnow
from ..schemas import (
    ApplicationListResponse,
    ApplicationOut,
    ApplicationUpdateRequest,
    ApproveResponse,
    DraftRequest,
    DraftResponse,
)
from ..services.resumes import latest_resume_or_error
from ..services.traces import record_audit, record_run, text_digest
from ..tools import html_to_text

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/draft", response_model=DraftResponse, status_code=201)
async def draft_application(
    req: DraftRequest,
    db: DbSession,
    session_id: SessionId,
) -> DraftResponse:
    resume = latest_resume_or_error(db, session_id)
    job = db.get(Job, req.job_id)
    if job is None or job.session_id != session_id:
        raise AppError(404, "job_not_found", "Search for this job first.")

    raw_job = job.raw if isinstance(job.raw, dict) else {}
    description = html_to_text(
        raw_job.get("jobDescription") or raw_job.get("jobExcerpt") or ""
    )

    started = time.perf_counter()
    resume_draft, cover_note, llm_meta = await orchestrator.docs.draft(
        resume.text,
        {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "skills": job.skills or [],
            "description": description,
        },
    )
    latency_ms = (time.perf_counter() - started) * 1000

    application = Application(
        session_id=session_id,
        job_id=job.id,
        company=job.company,
        title=job.title,
        url=job.url,
        deadline=job.deadline,
        status="PENDING_APPROVAL",
        resume_draft=resume_draft,
        cover_note=cover_note,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    record_run(
        db,
        session_id,
        agent="document",
        action="draft",
        output={
            "application_id": application.id,
            "job_id": job.id,
            "status": application.status,
            "llm": llm_meta,
        },
        latency_ms=latency_ms,
        input_text=f"{resume.text}\n{job.title}\n{job.company}",
    )
    record_audit(
        db,
        session_id,
        action="application_drafted",
        application_id=application.id,
        details={"status": application.status, "job_id": job.id},
    )

    return DraftResponse(
        application_id=application.id,
        status=application.status,
        resume_draft=application.resume_draft,
        cover_note=application.cover_note,
    )


@router.get("", response_model=ApplicationListResponse)
def list_applications(db: DbSession, session_id: SessionId) -> ApplicationListResponse:
    rows = list(
        db.scalars(
            select(Application)
            .where(Application.session_id == session_id)
            .order_by(Application.id.desc())
        )
    )
    return ApplicationListResponse(
        applications=[ApplicationOut.model_validate(row) for row in rows]
    )


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: int,
    req: ApplicationUpdateRequest,
    db: DbSession,
    session_id: SessionId,
) -> ApplicationOut:
    application = db.get(Application, app_id)
    if application is None or application.session_id != session_id:
        raise AppError(404, "application_not_found", "Application not found.")

    if application.status not in ("PENDING_APPROVAL", "APPROVED"):
        raise AppError(
            409,
            "invalid_status_transition",
            f"Cannot edit an application in status {application.status}.",
        )

    provided = req.model_dump(exclude_none=True)
    changed = {
        field: value
        for field, value in provided.items()
        if getattr(application, field) != value
    }
    if not changed:
        return ApplicationOut.model_validate(application)

    previous_status = application.status
    before_digests = {
        field: text_digest(getattr(application, field)) for field in changed
    }
    for field, value in changed.items():
        setattr(application, field, value)

    approval_reset = previous_status == "APPROVED"
    if approval_reset:
        application.status = "PENDING_APPROVAL"

    application.updated_at = utcnow()
    db.commit()
    db.refresh(application)

    record_audit(
        db,
        session_id,
        action="application_edited",
        application_id=application.id,
        details={
            "fields": sorted(changed),
            "previous_status": previous_status,
            "new_status": application.status,
            "approval_reset": approval_reset,
            "before_digests": before_digests,
            "after_digests": {
                field: text_digest(getattr(application, field)) for field in changed
            },
            "lengths": {
                field: len(getattr(application, field)) for field in changed
            },
        },
    )

    return ApplicationOut.model_validate(application)


@router.post("/{app_id}/approve", response_model=ApproveResponse)
def approve_application(
    app_id: int,
    db: DbSession,
    session_id: SessionId,
) -> ApproveResponse:
    application = db.get(Application, app_id)
    if application is None or application.session_id != session_id:
        raise AppError(404, "application_not_found", "Application not found.")

    if application.status == "APPROVED":
        return ApproveResponse(
            application_id=application.id,
            status=application.status,
            message="Application was already approved.",
        )

    if application.status != "PENDING_APPROVAL":
        raise AppError(
            409,
            "invalid_status_transition",
            f"Cannot approve an application in status {application.status}.",
        )

    if not orchestrator.applications.approval_required():
        raise AppError(409, "approval_disabled", "Approval is not required for this application.")

    previous_status = application.status
    application.status = "APPROVED"
    application.updated_at = utcnow()
    db.commit()
    db.refresh(application)

    record_audit(
        db,
        session_id,
        action="application_approved",
        application_id=application.id,
        details={"from": previous_status, "to": application.status},
    )

    return ApproveResponse(
        application_id=application.id,
        status=application.status,
        message=(
            "Approved by student. External submission remains a deliberate next step."
        ),
    )
