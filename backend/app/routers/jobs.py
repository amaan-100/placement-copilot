import time

from fastapi import APIRouter

from ..deps import DbSession, SessionId
from ..schemas import JobOut, JobSearchRequest, JobSearchResponse
from ..services.jobs import search_jobs
from ..services.resumes import latest_resume_or_error
from ..services.traces import record_run

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/search", response_model=JobSearchResponse)
async def jobs_search(
    req: JobSearchRequest,
    db: DbSession,
    session_id: SessionId,
) -> JobSearchResponse:
    resume = latest_resume_or_error(db, session_id)
    started = time.perf_counter()
    source, cached, ranked = await search_jobs(db, session_id, req.query, resume)
    latency_ms = (time.perf_counter() - started) * 1000

    record_run(
        db,
        session_id,
        agent="job",
        action="search",
        output={
            "query": req.query,
            "source": source,
            "cached": cached,
            "count": len(ranked),
        },
        latency_ms=latency_ms,
        input_text=req.query,
    )

    return JobSearchResponse(
        source=source,
        cached=cached,
        jobs=[JobOut(**job) for job in ranked],
    )
