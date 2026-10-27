# Architecture

```text
React/TypeScript SPA
  -> FastAPI routers and services
    -> session middleware (X-Session-Id + HttpOnly cookie)
    -> PlacementOrchestrator
      -> Resume | Job | Document | Interview | Application agents
        -> Ollama LLM provider (local HTTP API -> deterministic fallback)
        -> jobs provider (Jobicy live API -> mock fallback -> DB cache)
        -> PyMuPDF resume parser
    -> SQLAlchemy + Alembic (SQLite now, Postgres later)
    -> agent_runs and audit_events
```

## Request flow

1. `RequestContextMiddleware` assigns a request ID and emits JSON logs.
2. `SessionMiddleware` resolves or creates an anonymous session.
3. `RateLimitMiddleware` applies per-session limits.
4. Routers call services and agents; every query is scoped by `session_id`.
5. The response includes `X-Request-ID` and `X-Session-Id`.

## Data model

- `sessions` — anonymous workspace identity.
- `resumes` — extracted text and skill facts, scoped to a session.
- `jobs` — normalized live/mock jobs with stable internal IDs and a search TTL.
- `applications` — drafts with `PENDING_APPROVAL` -> `APPROVED` state.
- `interviews` — question, answer, score, and feedback.
- `agent_runs` — observable trace for every agent action.
- `audit_events` — approval and draft audit trail.

## Jobs

Live jobs are fetched from Jobicy and normalized. HTML is stripped before skill
extraction, and skills are deduplicated. The provider ranks matches against the
query, expands common synonyms, and keeps the strongest results. If the provider
fails or returns nothing, the Job Agent falls back to
`backend/data/mock_jobs.json`. Results are persisted so a live job can be drafted
by its internal database ID. Repeated searches are served from the database cache
until the TTL expires.

## Local LLM

`backend/app/providers/llm.py` calls Ollama's `/api/chat` endpoint with a strict
timeout and an optional JSON response format. Resume summaries, cover notes,
interview questions, and answer evaluations use the model when it is available.
Each call records provider, model, latency, and fallback reason in the agent trace.
If Ollama is offline, slow, or returns invalid output, the agents use their
deterministic implementations so the approval flow still works. Cover notes pass
a guard that rejects unsupported experience claims such as invented years,
previous roles, metrics, or certifications. The default model is
`qwen2.5-coder:7b`; set `LLM_PROVIDER=disabled` to force fallback mode.

## Approval state

`DRAFT` -> `PENDING_APPROVAL` -> `APPROVED`.

The approval endpoint is a real state-changing action. Approval is idempotent and
recorded in `audit_events`. There is intentionally no automatic third-party
submission endpoint, matching the requirement that nothing is sent without
student approval.

## Errors and limits

- Consistent error envelope with `error.code`, `error.message`, and `request_id`.
- PDF magic-byte validation, page and size limits, and filename sanitization.
- Per-session fixed-window rate limits, stricter for resume uploads.
- Readiness endpoint checks the database before reporting ready.

## Next

- Add an OpenAI-compatible backend behind the same LLM interface.
- Extend the structured resume profile and add fact-to-source citations.
- Multi-turn interview state machine.
- Docker Compose, Postgres, and CI.
