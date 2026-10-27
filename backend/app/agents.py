import re
from typing import Any

from .config import settings
from .providers.llm import complete_json, complete_text, fallback_meta
from .tools import (
    deterministic_document,
    evaluate_answer,
    interview_question,
    rank_jobs,
    resume_facts,
)

RESUME_SYSTEM = (
    "You extract structured facts from resumes. Return only valid JSON. "
    "Use only information explicitly present in the resume. Never invent "
    "employers, dates, degrees, metrics, or skills."
)

DOCUMENT_SYSTEM = (
    "You write concise, truthful application cover notes. Use only facts "
    "explicitly present in the candidate's resume. Never invent experience, "
    "metrics, degrees, or skills. Return plain text only."
)

QUESTION_SYSTEM = (
    "You are a technical interviewer. Ask one specific, answerable interview "
    "question for the target role. Return only the question."
)

EVALUATION_SYSTEM = (
    "You are a strict but constructive interview coach. Evaluate the answer "
    "for relevance, structure, evidence, and clarity. Return only valid JSON."
)


def _grounded_skills(
    payload: dict[str, Any],
    resume_text: str,
    deterministic: list[str],
) -> list[str]:
    low = resume_text.lower()
    skills = list(deterministic)
    seen = set(skills)
    raw = payload.get("skills")
    if not isinstance(raw, list):
        return skills

    for item in raw[:40]:
        if not isinstance(item, str):
            continue
        skill = " ".join(item.lower().split())
        if not skill or len(skill) > 60 or skill in seen:
            continue
        if skill in low:
            skills.append(skill)
            seen.add(skill)
    return skills[:24]


def _clean_summary(payload: dict[str, Any]) -> str | None:
    summary = payload.get("summary")
    if not isinstance(summary, str):
        return None
    cleaned = " ".join(summary.split())
    if not 30 <= len(cleaned) <= 500:
        return None
    return cleaned


UNSUPPORTED_CLAIM_PATTERNS = (
    r"\b\d+(?:\.\d+)?\+?\s*(?:years?|yrs?|months?|%|percent)\b",
    r"\bprevious (?:role|position|job)\b",
    r"\b(?:led|managed|increased|reduced|improved|achieved|awarded|certified|promoted)\b",
    r"\bcertification\b",
    r"\bmission\b",
    r"\bexpert\b",
)


def _unsupported_claim(text: str, resume: str) -> str | None:
    low_resume = resume.lower()
    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            claim = match.group(0).lower()
            if claim not in low_resume:
                return claim
    return None


def _clean_cover(value: str, resume: str) -> str | None:
    text = value.strip().strip("`").strip().strip('"').strip()
    marker = text.lower().find("dear hiring team")
    if marker == -1:
        return None
    text = text[marker:].strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not 80 <= len(text) <= 3500:
        return None
    if re.search(r"\[(?:company|role|name|date)[^\]]*\]", text, re.IGNORECASE):
        return None
    if _unsupported_claim(text, resume):
        return None
    return text


def _clean_question(value: str) -> str | None:
    text = " ".join(value.replace("`", "").strip().strip('"').split())
    text = re.split(r"(?<=\?)\s+", text, maxsplit=1)[0].strip()
    if not text:
        return None
    if not text.endswith("?"):
        text = f"{text}?"
    if not 15 <= len(text) <= 400:
        return None
    return text


def _clean_score(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        score = int(value)
    elif isinstance(value, str):
        match = re.search(r"\d+", value)
        if not match:
            return None
        score = int(match.group(0))
    else:
        return None
    return max(0, min(100, score))


def _clean_feedback(value: Any) -> str | None:
    if isinstance(value, (list, tuple)):
        value = " ".join(str(item) for item in value if isinstance(item, str))
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    if not 20 <= len(cleaned) <= 1000:
        return None
    return cleaned


class ResumeAgent:
    async def analyze(self, text: str) -> tuple[dict, dict[str, Any]]:
        facts = resume_facts(text)
        if not settings.llm_enabled:
            return facts, fallback_meta("disabled")

        prompt = (
            "Extract a concise candidate profile from the resume below.\n"
            "Return JSON with exactly these keys:\n"
            '- "summary": one or two sentences about the candidate\'s background.\n'
            '- "skills": an array of tools, languages, or domains named in the resume.\n'
            "Do not include contact details. Do not invent anything.\n\n"
            f"RESUME:\n{text[:12000]}"
        )
        payload, meta = await complete_json(RESUME_SYSTEM, prompt, max_tokens=350)
        if not payload:
            return facts, meta

        facts["skills"] = _grounded_skills(payload, text, facts["skills"])
        summary = _clean_summary(payload)
        if summary:
            facts["summary"] = summary
        return facts, meta


class JobAgent:
    def run(self, jobs: list[dict], resume: str, goal: str) -> list[dict]:
        return rank_jobs(jobs, resume_facts(resume)["skills"], goal)


class DocumentAgent:
    async def draft(
        self,
        resume: str,
        job: dict,
    ) -> tuple[str, str, dict[str, Any]]:
        resume_draft, fallback_cover = deterministic_document(resume, job)
        if not settings.llm_enabled:
            return resume_draft, fallback_cover, fallback_meta("disabled")

        prompt = (
            "Write a tailored cover note for this job in 120-170 words.\n"
            'Start exactly with "Dear Hiring Team," and end with "Sincerely," '
            "followed by the candidate's name only if it appears in the resume.\n"
            "Use only facts explicitly present in the resume below.\n"
            "Never add years of experience, previous job titles, employers, "
            "metrics, certifications, awards, or company mission claims.\n"
            "You may mention the target job title, company, and required skills, "
            "but do not claim the candidate has experience they do not have.\n"
            "Do not use placeholder brackets or markdown.\n\n"
            f"JOB TITLE: {job.get('title', '')}\n"
            f"COMPANY: {job.get('company', '')}\n"
            f"LOCATION: {job.get('location', '')}\n"
            f"JOB SKILLS: {', '.join(job.get('skills') or [])}\n"
            f"JOB DESCRIPTION:\n{(job.get('description') or '')[:4000]}\n\n"
            f"RESUME FACTS (verbatim):\n{resume[:12000]}"
        )
        cover, meta = await complete_text(DOCUMENT_SYSTEM, prompt, max_tokens=450)
        if not cover:
            return resume_draft, fallback_cover, meta

        cleaned = _clean_cover(cover, resume)
        if not cleaned:
            return resume_draft, fallback_cover, {
                **meta,
                "used": False,
                "error": "invalid_output",
            }
        return resume_draft, cleaned, meta


class InterviewAgent:
    async def question(self, goal: str) -> tuple[str, dict[str, Any]]:
        fallback = interview_question(goal)
        if not settings.llm_enabled:
            return fallback, fallback_meta("disabled")

        prompt = (
            f"Target role: {goal}\n"
            "Ask one interview question that tests a relevant skill or scenario. "
            "It should be answerable in 60-90 seconds. Return only the question."
        )
        content, meta = await complete_text(QUESTION_SYSTEM, prompt, max_tokens=120)
        if not content:
            return fallback, meta

        cleaned = _clean_question(content)
        if not cleaned:
            return fallback, {**meta, "used": False, "error": "invalid_output"}
        return cleaned, meta

    async def evaluate(
        self,
        goal: str,
        question: str,
        answer: str,
    ) -> tuple[int, str, dict[str, Any]]:
        fallback_score, fallback_feedback = evaluate_answer(answer)
        if not settings.llm_enabled:
            return fallback_score, fallback_feedback, fallback_meta("disabled")

        prompt = (
            "Evaluate the candidate's answer using this rubric:\n"
            "- Relevance to the question: 30\n"
            "- Structure and clarity: 25\n"
            "- Evidence and concrete examples: 25\n"
            "- Technical accuracy: 20\n\n"
            'Return JSON with exactly two keys: "score" (integer 0-100) and '
            '"feedback" (2-3 specific, actionable sentences).\n\n'
            f"TARGET ROLE: {goal}\n"
            f"QUESTION: {question}\n"
            f"ANSWER:\n{answer[:5000]}"
        )
        payload, meta = await complete_json(
            EVALUATION_SYSTEM,
            prompt,
            max_tokens=300,
        )
        if not payload:
            return fallback_score, fallback_feedback, meta

        score = _clean_score(payload.get("score"))
        feedback = _clean_feedback(payload.get("feedback"))
        if score is None or feedback is None:
            return fallback_score, fallback_feedback, {
                **meta,
                "used": False,
                "error": "invalid_output",
            }
        return score, feedback, meta


class ApplicationAgent:
    def approval_required(self) -> bool:
        return True


class PlacementOrchestrator:
    def __init__(self) -> None:
        self.resume = ResumeAgent()
        self.jobs = JobAgent()
        self.docs = DocumentAgent()
        self.interview = InterviewAgent()
        self.applications = ApplicationAgent()


orchestrator = PlacementOrchestrator()
