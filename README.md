# Placement Co-pilot — AgentX Hackathon PS-06

An approval-gated, multi-agent placement assistant. Upload a resume, search and
rank jobs, draft a tailored application, approve it explicitly, and practice an
interview.

## Agents

- Resume Agent — extracts skills, a short profile summary, and facts from a PDF.
- Job Agent — fetches live jobs from Jobicy, filters them against the query,
  falls back to mock listings, persists results, and ranks them against the resume.
- Document Agent — uses a local Ollama model to write a job-specific cover note,
  falling back to a deterministic draft when the model is unavailable.
- Interview Agent — asks a role-specific question and scores the answer with
  rubric-based feedback, using Ollama when available.
- Application Agent — enforces the approval gate and records an audit trail.
- Placement Orchestrator — coordinates the agents and stores an agent trace.

## Approval safety

Applications are never submitted automatically. Drafts enter
`PENDING_APPROVAL`, and the student must explicitly approve. The prototype has no
third-party submission endpoint. Every draft and approval is recorded in
`agent_runs` and `audit_events`.

## Stack

FastAPI, SQLAlchemy, Alembic, SQLite, PyMuPDF, Ollama; React, TypeScript, Vite.

## Local LLM (Ollama)

The app uses a local Ollama model for resume summaries, cover notes, interview
questions, and answer feedback. Every generation has a deterministic fallback, so
the demo still works when Ollama is stopped.

```bash
ollama serve
ollama pull qwen2.5-coder:7b
```

Check that the backend can see the model:

```bash
curl http://127.0.0.1:8000/api/llm/status
```

Expected fields include `"reachable": true` and `"model_available": true`. To force
deterministic mode, set `LLM_PROVIDER=disabled` in `backend/.env` and restart the
backend.

## Run the backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Alembic migrations run automatically on startup.
To run them manually:

```bash
alembic upgrade head
```

## Run the tests

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

Tests use an isolated SQLite database, the mock jobs provider, and
`LLM_PROVIDER=disabled`, so they do not need network access.

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Production build:

```bash
npm run build
npm run preview
```

## Verify the full flow

1. Start Ollama, the backend, and the frontend. Open
   http://127.0.0.1:5173 and confirm the **Local AI** panel shows
   `qwen2.5-coder:7b` and "Local generation is enabled".
2. Upload a text-based PDF. Confirm the resume summary, skills, and a
   `ollama/qwen2.5-coder:7b` trace badge appear.
3. Search for a role, draft an application, and open **Review and approve**.
   The cover note should use only resume facts and should not invent years,
   previous roles, metrics, or certifications.
4. Approve the draft, start practice, submit an answer, and confirm rubric
   feedback plus a second Ollama trace.
5. Test fallback: stop Ollama (or set `LLM_PROVIDER=disabled` and restart the
   backend). The app should stay usable, show fallback mode, and still complete
   the flow with deterministic content.
6. A 404 on `/api/resume/latest` in the browser console before the first upload
   is expected.

## Sessions

The frontend creates an anonymous session UUID and sends it as
`X-Session-Id`. All resumes, jobs, applications, interviews, traces, and audit
events are scoped to that session. The backend also sets an `HttpOnly` cookie as a
fallback.

## Configuration

Copy `backend/.env.example` and adjust as needed. Useful settings:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///placement.db` | SQLAlchemy database URL |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |
| `JOBS_PROVIDER` | `auto` | `auto`, `live`, or `mock` |
| `JOBS_API_URL` | `https://jobicy.com/api/v2/remote-jobs` | Live job source |
| `JOBS_FETCH_COUNT` | `50` | Jobs fetched before query filtering |
| `JOBS_CACHE_TTL_SECONDS` | `3600` | Cached job search TTL |
| `LLM_PROVIDER` | `auto` | `auto`, `ollama`, or `disabled` |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama server |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Model used for generation |
| `LLM_TIMEOUT_SECONDS` | `90` | Per-request Ollama timeout |
| `LLM_MAX_TOKENS` | `600` | Maximum generated tokens |
| `LLM_CONTEXT_TOKENS` | `8192` | Ollama context window |
| `MAX_UPLOAD_BYTES` | `8388608` | PDF upload limit |
| `RATE_LIMIT_REQUESTS` | `120` | General API requests per window |
| `RATE_LIMIT_UPLOAD_REQUESTS` | `12` | Resume uploads per window |

## API overview

- `GET /api/health`, `GET /api/llm/status`, `GET /healthz`, `GET /readyz`
- `GET /api/session`
- `POST /api/resume/upload`, `GET /api/resume/latest`, `DELETE /api/resume/current`
- `POST /api/jobs/search`
- `POST /api/applications/draft`, `GET /api/applications`,
  `POST /api/applications/{id}/approve`
- `POST /api/interviews`, `POST /api/interviews/{id}/evaluate`
- `GET /api/dashboard`, `GET /api/traces`

Errors use a consistent envelope:

```json
{
  "error": {"code": "job_not_found", "message": "Search for this job first."},
  "request_id": "..."
}
```

## Production notes

- Pin Python 3.12 in Docker/CI; local Python 3.14 works with `pydantic>=2.12`.
- SQLite with WAL is fine for a single instance. Use Postgres for multiple workers.
- Generate content with an LLM only behind a provider abstraction with a
  deterministic fallback; never fabricate resume facts.
- Export approved drafts and add email/calendar reminders next.
- See [docs/plan.md](docs/plan.md) for the full production roadmap.
