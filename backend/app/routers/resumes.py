import logging
import os
import re
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from sqlalchemy import select

from ..agents import orchestrator
from ..config import settings
from ..deps import DbSession, SessionId
from ..errors import AppError
from ..models import Resume
from ..schemas import ResumeResponse, ResumeUploadResponse
from ..services.resumes import latest_resume
from ..services.traces import record_run
from ..tools import extract_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["resumes"])


def sanitize_filename(name: str | None) -> str:
    base = Path(name or "resume.pdf").name
    base = re.sub(r"[^A-Za-z0-9._ -]", "_", base).strip(" .")
    if not base:
        base = "resume.pdf"
    if not base.lower().endswith(".pdf"):
        base = f"{base}.pdf"
    return base[:255]


@router.post("/upload", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(
    db: DbSession,
    session_id: SessionId,
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    original_name = file.filename or "resume.pdf"
    if not original_name.lower().endswith(".pdf"):
        raise AppError(400, "invalid_file_type", "Only PDF resumes are accepted.")

    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise AppError(413, "file_too_large", "PDF exceeds the upload size limit.")
    if not data.startswith(settings.pdf_magic_bytes.encode("ascii")):
        raise AppError(422, "invalid_pdf", "The uploaded file is not a valid PDF.")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(data)
        path = tmp.name

    started = time.perf_counter()
    try:
        text = extract_pdf(path)
    except ValueError as exc:
        raise AppError(422, "pdf_unreadable", str(exc)) from None
    except Exception:
        logger.exception("pdf_parse_failed")
        raise AppError(422, "pdf_unreadable", "Could not extract text from the PDF.") from None
    finally:
        try:
            os.unlink(path)
        except OSError:
            logger.warning("temp_pdf_cleanup_failed", extra={"path": path})

    text = text.strip()
    if not text:
        raise AppError(422, "empty_resume", "No readable text was found in the PDF.")
    if len(text) > settings.max_resume_chars:
        text = text[: settings.max_resume_chars]

    facts, llm_meta = await orchestrator.resume.analyze(text)
    safe_facts = {"skills": facts.get("skills", [])}
    if facts.get("summary"):
        safe_facts["summary"] = facts["summary"]
    resume = Resume(
        session_id=session_id,
        filename=sanitize_filename(original_name),
        text=text,
        facts=safe_facts,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    latency_ms = (time.perf_counter() - started) * 1000
    record_run(
        db,
        session_id,
        agent="resume",
        action="analyze",
        output={
            "resume_id": resume.id,
            "skills": safe_facts["skills"],
            "characters": len(text),
            "llm": llm_meta,
        },
        latency_ms=latency_ms,
        input_text=text,
    )

    return ResumeUploadResponse(
        resume_id=resume.id,
        filename=resume.filename,
        facts=safe_facts,
        created_at=resume.created_at,
    )


@router.get("/latest", response_model=ResumeResponse)
def get_latest_resume(db: DbSession, session_id: SessionId) -> ResumeResponse:
    resume = latest_resume(db, session_id)
    if resume is None:
        raise AppError(404, "resume_not_found", "Upload a resume first.")
    return ResumeResponse.model_validate(resume)


@router.delete("/current")
def delete_resumes(db: DbSession, session_id: SessionId) -> dict:
    resumes = list(db.scalars(select(Resume).where(Resume.session_id == session_id)))
    for resume in resumes:
        db.delete(resume)
    db.commit()
    return {"deleted": len(resumes)}
