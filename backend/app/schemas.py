from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=160)

    @field_validator("query")
    @classmethod
    def clean_query(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 2:
            raise ValueError("Query must contain at least two non-space characters.")
        return cleaned


class DraftRequest(BaseModel):
    job_id: int = Field(gt=0)


class InterviewStartRequest(BaseModel):
    goal: str = Field(min_length=2, max_length=160)

    @field_validator("goal")
    @classmethod
    def clean_goal(cls, value: str) -> str:
        return " ".join(value.split())


class InterviewEvaluateRequest(BaseModel):
    interview_id: int = Field(gt=0)
    answer: str = Field(min_length=1, max_length=5000)

    @field_validator("answer")
    @classmethod
    def clean_answer(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Answer cannot be empty.")
        return cleaned


class ResumeUploadResponse(BaseModel):
    resume_id: int
    filename: str
    facts: dict[str, Any]
    created_at: datetime


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    facts: dict[str, Any]
    created_at: datetime


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    location: str
    url: str
    skills: list[str]
    deadline: str | None
    match_score: int
    source: str


class JobSearchResponse(BaseModel):
    source: str
    cached: bool
    jobs: list[JobOut]


class DraftResponse(BaseModel):
    application_id: int
    status: str
    resume_draft: str
    cover_note: str


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: int | None
    company: str
    title: str
    url: str
    deadline: str | None
    status: str
    resume_draft: str
    cover_note: str
    created_at: datetime
    updated_at: datetime


class ApplicationUpdateRequest(BaseModel):
    resume_draft: str | None = Field(default=None, max_length=20_000)
    cover_note: str | None = Field(default=None, max_length=8_000)

    @field_validator("resume_draft", "cover_note")
    @classmethod
    def clean_draft(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Draft text cannot be empty.")
        return cleaned

    @model_validator(mode="after")
    def require_draft_field(self) -> "ApplicationUpdateRequest":
        if self.resume_draft is None and self.cover_note is None:
            raise ValueError("Provide at least one draft field.")
        return self


class ApplicationListResponse(BaseModel):
    applications: list[ApplicationOut]


class ApproveResponse(BaseModel):
    application_id: int
    status: str
    message: str


class InterviewStartResponse(BaseModel):
    interview_id: int
    question: str
    status: str


class InterviewEvaluateResponse(BaseModel):
    interview_id: int
    score: int
    feedback: str
    status: str


class DashboardResponse(BaseModel):
    applications: int
    pending_approvals: int
    interviews: int
    approved: int


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    agent: str
    approval_gate: bool


class LlmStatusResponse(BaseModel):
    enabled: bool
    available: bool


class AgentTraceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent: str
    action: str
    status: str
    latency_ms: int
    output: dict[str, Any]
    created_at: datetime
