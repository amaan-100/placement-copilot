# Production-Ready Hackathon Plan

This plan turns the Placement Co-pilot demo into a reliable, judge-ready product.
"Production-ready" here means a hardened single-instance deployment: real data,
guarded generation, session isolation, an auditable approval gate, tests, and a
repeatable deploy. It does not mean a multi-tenant SaaS.

## Current gaps

- Generation supports local Ollama and an OpenAI-compatible cloud gateway; there
  is no automatic provider failover yet.
- Data is scoped to an anonymous browser session; there are no user accounts.
- Interview is a single question, not yet a multi-turn state machine.
- Generated content is not yet fact-cited or user-editable.
- Docker, CI, and a seeded demo script are not set up yet.

## Definition of done

1. Upload a real PDF and receive a validated structured profile.
2. Search live jobs, persist them, and draft against them.
3. Generate tailored content with zero fabricated resume facts.
4. Enforce approval server-side with an audit trail.
5. Run a multi-turn interview with rubric-based feedback.
6. Survive bad input, job API outages, and LLM timeouts without crashing.
7. Deploy via Docker, pass tests, and show an agent trace in the UI.

## Target architecture

```text
React/TS SPA
  -> FastAPI routers/services
    -> PlacementOrchestrator (typed state machine)
      -> Resume | Job | Document | Interview | Application agents
        -> LLM provider (Ollama/OpenAI-compatible) + deterministic fallback
        -> Jobs provider (Jobicy + query filtering + cache + mock)
        -> PDF provider (PyMuPDF)
    -> SQLite/Postgres + audit log
  -> Caddy/nginx
```

Differentiators for judges: visible agent trace, fact-cited generated content,
and a hard approval gate.

## Workstreams

### P0 - Must ship

**Backend foundation**
- `config.py` with `pydantic-settings`, `.env.example`, and a `lifespan`.
- SQLAlchemy models and Alembic migrations; WAL, foreign keys, indexes.
- Anonymous session middleware; scope every query by session.
- Structured JSON logging, request IDs, consistent errors, rate limits.
- Replace deprecated `@app.on_event`.

**Real agent layer**
- [x] `providers/llm.py`: Ollama and OpenAI-compatible providers, timeouts, JSON
  mode, deterministic fallback, and a cached status endpoint.
- [x] Resume Agent: grounded skills plus a short local-LLM summary.
- [ ] Extend resume extraction to contact, education, experience, and projects.
- [x] Job Agent: normalize, dedupe, persist live jobs with stable DB IDs, cache
  with TTL, and rank deterministically.
- [x] Document Agent: local-LLM cover note when available, deterministic fallback.
- [ ] Fact-to-source citations and user editing for generated content.
- [ ] Interview Agent: state machine with follow-ups and a transcript.
- [x] Orchestrator: server-side per-run trace with provider/model metadata; public traces sanitized.

**Fix the live-job gap**
- Cache jobs in the database. Draft by internal `job_id`, not only mock IDs.

**API**
- `/sessions`, `/resumes`, `/jobs/search`, `/jobs/{id}`,
  `/applications/draft`, `/applications/{id}/approve`,
  `/applications/{id}/export`, `/interviews`, `/interviews/{id}/answers`,
  `/dashboard`, `/healthz`, `/readyz`.
- Typed models, pagination where needed, idempotent approval.

**Frontend**
- Component/page split with TypeScript.
- API client with errors, retries, timeouts, and loading states.
- Wizard: Upload -> Profile -> Jobs -> Tailor -> Approve -> Interview.
- Approval modal with preview and explicit confirmation.
- Empty/error/offline states, responsive layout, keyboard accessibility.
- Agent trace panel and dashboard timeline.

**Security/privacy**
- Validate PDF magic bytes, size limits, filename sanitization, parser timeout.
- Treat job descriptions as untrusted data to resist prompt injection.
- Sanitize generated markdown; add CSP; CORS allowlist from env.
- Resume delete endpoint and a retention note.
- Never auto-submit applications; submission stays a deliberate action.

### P1 - Should ship

- Playwright E2E: happy path, bad PDF, API down, approval gate.
- Pytest: parsing, ranking, no-hallucination contract, session isolation,
  state transitions.
- Docker Compose and multi-stage builds; pin Python 3.12 in Docker.
- GitHub Actions: ruff, mypy, pytest, frontend build, Playwright smoke.
- Seed script with sample resumes and a deterministic demo mode.
- Export approved drafts to PDF or `.docx`.
- Skill-gap analysis and a learning plan from ranked jobs.

### P2 - Stretch

- Email/calendar reminders.
- Browser-extension autofill behind approval.
- RAG over job descriptions.
- Model routing and a cost dashboard.
- Evaluation harness comparing agent versions.

## Three-day schedule

| Day | Deliverable | Demo checkpoint |
|---|---|---|
| 1 AM | Config, lifespan, migrations, sessions, CI, test skeleton | Isolated sessions, clean errors |
| 1 PM | LLM provider, resume profile, job persistence/ranking | Upload -> profile -> saved live jobs |
| 2 AM | Document + interview agents, fact mapping, fallback | Tailored draft and multi-turn interview |
| 2 PM | Frontend rewrite, approval flow, trace panel | Full happy path in browser |
| 3 AM | Security, tests, Docker, deploy, performance | Bad input and outage handling |
| 3 PM | Seed data, demo script, backup recording, buffer | Five-minute judge demo |

## Risks and cut list

- LLM latency/outage: streaming, timeouts, deterministic fallback; pre-warm.
- Live jobs API failure: DB cache and a visible mock fallback toggle.
- Hallucinated resume content: fact-to-source mapping and user editing.
- Scope creep: no real ATS submissions, no full auth, no native mobile.
- SQLite concurrency: WAL and a single worker, or Postgres for multi-user.
- Wheel/build issues: Python 3.12 in Docker and CI.

## First four hours

- [x] Save this plan and create the task list.
- [x] Add config, lifespan, error handlers, structured logging, rate limits.
- [x] Add sessions, SQLAlchemy models, and Alembic migrations.
- [x] Persist live jobs and draft by internal job ID.
- [x] Add pytest happy-path and approval-transition tests.
- [x] Split the frontend into components with a typed API client.
- [x] Add local Ollama generation with a deterministic fallback.
- [x] Show generic AI/fallback status in the UI; keep provider/model metadata server-side.
