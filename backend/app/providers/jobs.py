import logging
import re
from typing import Any

import httpx

from ..config import settings
from ..errors import AppError
from ..tools import SKILL_VOCABULARY, extract_skills, html_to_text, local_jobs

logger = logging.getLogger(__name__)

TOKEN_RE = re.compile(r"[a-z0-9+#.]+")

STOPWORDS = {
    "a",
    "an",
    "and",
    "entry",
    "for",
    "in",
    "job",
    "jobs",
    "level",
    "of",
    "on",
    "or",
    "remote",
    "role",
    "the",
    "to",
    "with",
}

TERM_EXPANSIONS = {
    "analyst": ("analysis", "analytics"),
    "cybersecurity": (
        "security",
        "infosec",
        "soc",
        "threat",
        "vulnerability",
        "incident",
        "penetration",
        "detection",
        "phishing",
    ),
    "designer": ("design",),
    "developer": ("engineer", "development"),
    "engineer": ("developer", "engineering"),
    "intern": ("internship", "new grad"),
    "internship": ("intern", "new grad"),
    "marketing": ("growth", "seo"),
    "sales": ("account executive", "business development"),
    "security": (
        "cybersecurity",
        "infosec",
        "soc",
        "threat",
        "vulnerability",
        "incident",
        "penetration",
        "detection",
        "phishing",
    ),
    "writer": ("writing", "content"),
}


def _unique_skills(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    skills: list[str] = []
    for value in values:
        skill = str(value or "").strip().lower()
        if not skill or skill in seen:
            continue
        seen.add(skill)
        skills.append(skill)
    return skills


def _normalize_live_job(job: dict[str, Any]) -> dict[str, Any]:
    description = html_to_text(job.get("jobDescription") or job.get("jobExcerpt") or "")
    industries = job.get("jobIndustry") or []
    if isinstance(industries, str):
        industries = [industries]
    return {
        "external_id": str(job.get("id") or job.get("jobSlug") or ""),
        "title": job.get("jobTitle") or "Untitled role",
        "company": job.get("companyName") or "Unknown company",
        "location": job.get("jobGeo") or "Remote",
        "url": job.get("url") or "",
        "skills": _unique_skills([*industries, *extract_skills(description)])[:12],
        "deadline": None,
        "raw": job,
    }


def _normalize_mock_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "external_id": str(job["id"]),
        "title": job.get("title") or "Untitled role",
        "company": job.get("company") or "Unknown company",
        "location": job.get("location") or "Remote",
        "url": job.get("url") or "",
        "skills": _unique_skills(list(job.get("skills") or [])),
        "deadline": job.get("deadline"),
        "raw": job,
    }


def _query_terms(query: str) -> list[str]:
    return [
        token
        for token in TOKEN_RE.findall((query or "").lower())
        if len(token) >= 2 and token not in STOPWORDS
    ]


def _primary_tag(terms: list[str]) -> str | None:
    for term in terms:
        if term in SKILL_VOCABULARY:
            return term
    for term in terms:
        if len(term) >= 4:
            return term
    return None


def _has(text: str, phrase: str) -> bool:
    pattern = rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def _score_job(job: dict[str, Any], terms: list[str]) -> int:
    title = job["title"].lower()
    score = 0
    for term in terms:
        if _has(title, term):
            score += 4
        for expansion in TERM_EXPANSIONS.get(term, ()):
            if _has(title, expansion):
                score += 3
    return score


def _select_jobs(
    jobs: list[dict[str, Any]],
    query: str,
    fallback: bool = True,
) -> list[dict[str, Any]]:
    terms = _query_terms(query)
    if not terms:
        return jobs[: settings.jobs_max_results] if fallback else []
    scored = sorted(
        ((_score_job(job, terms), job) for job in jobs),
        key=lambda item: item[0],
        reverse=True,
    )
    matching = [job for score, job in scored if score >= 3]
    if matching:
        return matching[: settings.jobs_max_results]
    return [job for _, job in scored][: settings.jobs_max_results] if fallback else []


async def _fetch_payload(tag: str | None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"count": settings.jobs_fetch_count}
    if tag:
        params["tag"] = tag

    async with httpx.AsyncClient(timeout=settings.jobs_api_timeout_seconds) as client:
        response = await client.get(settings.jobs_api_url, params=params)
        response.raise_for_status()
        data = response.json()

    jobs = [
        _normalize_live_job(job)
        for job in (data.get("jobs") or [])
        if isinstance(job, dict)
    ]
    return [job for job in jobs if job["external_id"]]


async def fetch_live_jobs(query: str) -> list[dict[str, Any]]:
    tag = _primary_tag(_query_terms(query))
    jobs = await _fetch_payload(tag) if tag else []
    selected = _select_jobs(jobs, query, fallback=False) if tag else []

    if not selected:
        jobs = await _fetch_payload(None)
        selected = _select_jobs(jobs, query)

    return selected


def fetch_mock_jobs() -> list[dict[str, Any]]:
    return [_normalize_mock_job(job) for job in local_jobs()]


async def fetch_jobs(query: str) -> tuple[list[dict[str, Any]], str]:
    provider = settings.jobs_provider
    if provider == "mock":
        return fetch_mock_jobs(), "mock_fallback"

    try:
        jobs = await fetch_live_jobs(query)
        if jobs:
            return jobs, "live_api"
        logger.warning("jobs_live_empty", extra={"agent": "job"})
    except (httpx.HTTPError, ValueError):
        logger.warning("jobs_live_failed", exc_info=True, extra={"agent": "job"})
        if provider == "live":
            raise AppError(
                503,
                "jobs_unavailable",
                "The live jobs provider is unavailable. Try the mock provider.",
            ) from None

    return fetch_mock_jobs(), "mock_fallback"
