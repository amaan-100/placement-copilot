import time

from fastapi import APIRouter

from ..agents import orchestrator
from ..deps import DbSession, SessionId
from ..errors import AppError
from ..models import Interview
from ..schemas import (
    InterviewEvaluateRequest,
    InterviewEvaluateResponse,
    InterviewStartRequest,
    InterviewStartResponse,
)
from ..services.traces import record_run

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post("", response_model=InterviewStartResponse, status_code=201)
async def start_interview(
    req: InterviewStartRequest,
    db: DbSession,
    session_id: SessionId,
) -> InterviewStartResponse:
    started = time.perf_counter()
    question, llm_meta = await orchestrator.interview.question(req.goal)
    interview = Interview(
        session_id=session_id,
        goal=req.goal,
        question=question,
        status="OPEN",
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)
    latency_ms = (time.perf_counter() - started) * 1000

    record_run(
        db,
        session_id,
        agent="interview",
        action="question",
        output={
            "interview_id": interview.id,
            "goal": req.goal,
            "llm": llm_meta,
        },
        latency_ms=latency_ms,
        input_text=req.goal,
    )

    return InterviewStartResponse(
        interview_id=interview.id,
        question=interview.question,
        status=interview.status,
    )


@router.post("/{interview_id}/evaluate", response_model=InterviewEvaluateResponse)
async def evaluate_interview(
    interview_id: int,
    req: InterviewEvaluateRequest,
    db: DbSession,
    session_id: SessionId,
) -> InterviewEvaluateResponse:
    if req.interview_id != interview_id:
        raise AppError(400, "interview_mismatch", "Interview ID does not match the request body.")
    interview = db.get(Interview, interview_id)
    if interview is None or interview.session_id != session_id:
        raise AppError(404, "interview_not_found", "Interview not found.")

    started = time.perf_counter()
    score, feedback, llm_meta = await orchestrator.interview.evaluate(
        interview.goal,
        interview.question,
        req.answer,
    )
    latency_ms = (time.perf_counter() - started) * 1000

    interview.answer = req.answer
    interview.score = score
    interview.feedback = feedback
    interview.status = "EVALUATED"
    db.commit()
    db.refresh(interview)

    record_run(
        db,
        session_id,
        agent="interview",
        action="evaluate",
        output={
            "interview_id": interview.id,
            "score": score,
            "status": interview.status,
            "llm": llm_meta,
        },
        latency_ms=latency_ms,
        input_text=req.answer,
    )

    return InterviewEvaluateResponse(
        interview_id=interview.id,
        score=score,
        feedback=feedback,
        status=interview.status,
    )
