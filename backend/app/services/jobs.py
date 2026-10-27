from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Job, Resume, utcnow
from ..providers.jobs import fetch_jobs
from ..tools import rank_jobs


def _cache_cutoff():
    return utcnow() - timedelta(seconds=settings.jobs_cache_ttl_seconds)


def _cached_rows(db: Session, session_id: str, query: str) -> list[Job]:
    return list(
        db.scalars(
            select(Job)
            .where(
                Job.session_id == session_id,
                Job.query == query,
                Job.fetched_at >= _cache_cutoff(),
            )
            .order_by(Job.id)
        )
    )


def _latest_source(rows: list[Job]) -> str:
    latest = max(rows, key=lambda job: job.fetched_at)
    return latest.source


def _persist(
    db: Session,
    session_id: str,
    query: str,
    fetched: list[dict],
    source: str,
) -> list[Job]:
    external_ids = [item["external_id"] for item in fetched]
    existing_rows = list(
        db.scalars(
            select(Job).where(
                Job.session_id == session_id,
                Job.source == source,
                Job.external_id.in_(external_ids),
            )
        )
    )
    existing = {job.external_id: job for job in existing_rows}
    now = utcnow()

    for item in fetched:
        row = existing.get(item["external_id"])
        if row is None:
            row = Job(
                session_id=session_id,
                external_id=item["external_id"],
                source=source,
                query=query,
                title=item["title"],
                company=item["company"],
                location=item["location"],
                url=item["url"],
                skills=item["skills"],
                deadline=item["deadline"],
                raw=item["raw"],
                fetched_at=now,
            )
            db.add(row)
        else:
            row.query = query
            row.title = item["title"]
            row.company = item["company"]
            row.location = item["location"]
            row.url = item["url"]
            row.skills = item["skills"]
            row.deadline = item["deadline"]
            row.raw = item["raw"]
            row.fetched_at = now

    db.commit()
    return list(
        db.scalars(
            select(Job)
            .where(
                Job.session_id == session_id,
                Job.source == source,
                Job.query == query,
                Job.fetched_at >= _cache_cutoff(),
            )
            .order_by(Job.id)
        )
    )


def _ranked_payload(rows: list[Job], resume: Resume, query: str) -> list[dict]:
    facts = resume.facts or {}
    skills = list(facts.get("skills") or [])
    payload = [
        {
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "url": job.url,
            "skills": job.skills or [],
            "deadline": job.deadline,
            "source": job.source,
        }
        for job in rows
    ]
    return rank_jobs(payload, skills, query)


async def search_jobs(
    db: Session,
    session_id: str,
    query: str,
    resume: Resume,
) -> tuple[str, bool, list[dict]]:
    rows = _cached_rows(db, session_id, query)
    cached = bool(rows)

    if cached:
        source = _latest_source(rows)
        rows = [job for job in rows if job.source == source]
    else:
        fetched, source = await fetch_jobs(query)
        rows = _persist(db, session_id, query, fetched, source)

    return source, cached, _ranked_payload(rows, resume, query)
