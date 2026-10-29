# Placement Co-pilot — AgentX Hackathon PS-06

An approval-gated, multi-agent placement assistant. Upload a resume, search and
rank jobs, draft a tailored application, approve it explicitly, and practice an
interview.

## Agents

- Resume Agent — extracts skills, a short profile summary, and facts from a PDF.
- Job Agent — fetches live jobs from Jobicy, filters them against the query,
  falls back to mock listings, persists results, and ranks them against the resume.
- Document Agent — uses the configured LLM provider to write a job-specific cover
  note, falling back to a deterministic draft when the model is unavailable.
- Interview Agent — asks a role-specific question and scores the answer with
  rubric-based feedback, using the configured LLM provider when available.
- Application Agent — enforces the approval gate and records an audit trail.
- Placement Orchestrator — coordinates the agents and stores an agent trace.

## Approval safety

Applications are never submitted automatically. Drafts enter
`PENDING_APPROVAL`, and the student must explicitly approve. The prototype has no
third-party submission endpoint. Every draft and approval is recorded in
`agent_runs` and `audit_events`.

## Stack

FastAPI, SQLAlchemy, Alembic, SQLite locally / Neon Postgres in production,
PyMuPDF, Ollama or an OpenAI-compatible gateway; React, TypeScript, Vite.

## LLM providers

The app uses the configured LLM provider for resume summaries, cover notes,
interview questions, and answer feedback. Every generation has a deterministic
fallback, so the demo still works when the provider is unavailable.

### Local Ollama

```bash
ollama serve
ollama pull qwen2.5-coder:7b
```

Set `LLM_PROVIDER=ollama` in `backend/.env`, then check that the backend can see
the model:

```bash
curl http://127.0.0.1:8000/api/llm/status
```

The public response only exposes `enabled` and `available`; provider, model,
endpoint, and model-list details stay server-side.

### Cloud OpenAI-compatible gateway

Requesty and similar gateways can serve the app through the generic
`openai_compatible` provider. Put the key only in `backend/.env`; never expose it
to the frontend or commit it.

```dotenv
LLM_PROVIDER=openai_compatible
LLM_PROVIDER_LABEL=requesty
LLM_BASE_URL=https://router.requesty.ai/v1
LLM_API_KEY=<your-key>
LLM_MODEL=google/gemma-4-31b-it
```

Requesty's free tier allows 200 requests per day and 20 requests per minute, and
only free models are available without billing. Check `/api/llm/status` after a
restart and adjust `LLM_MODEL` to a model that the account can actually access.

To force deterministic mode, set `LLM_PROVIDER=disabled` in `backend/.env` and
restart the backend.

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

1. Start the configured LLM provider, the backend, and the frontend. Open
   http://127.0.0.1:5173 and confirm the **AI assistance** panel shows readiness,
   not a provider name, endpoint, or model.
2. Upload a text-based PDF. Confirm the resume summary, skills, and a generic
   AI-assisted or template-fallback trace badge appear.
3. Search for a role, draft an application, and open **Review draft**. Edit the
   cover note or resume draft, save, and confirm the edited text persists.
4. Approve the draft. Reopen the approved draft, change the text, and confirm
   approval resets to `PENDING_APPROVAL`; approve the new text again.
5. Start practice, submit an answer, and confirm rubric feedback plus a second
   generic AI/fallback trace.
6. Test fallback: stop the provider (or set `LLM_PROVIDER=disabled` and restart
   the backend). The app should stay usable, show fallback drafting, and still
   complete the flow with deterministic content.
7. A 404 on `/api/resume/latest` in the browser console before the first upload
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
| `DATABASE_URL` | `sqlite:///placement.db` | SQLAlchemy URL; Neon uses `postgresql+psycopg://...?...sslmode=require` |
| `DB_POOL_SIZE` | `5` | Postgres connection pool size |
| `DB_MAX_OVERFLOW` | `5` | Postgres pool overflow |
| `DB_POOL_RECYCLE_SECONDS` | `300` | Recycle idle Postgres connections |
| `DB_CONNECT_TIMEOUT_SECONDS` | `10` | Postgres connection timeout |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |
| `JOBS_PROVIDER` | `auto` | `auto`, `live`, or `mock` |
| `JOBS_API_URL` | `https://jobicy.com/api/v2/remote-jobs` | Live job source |
| `JOBS_FETCH_COUNT` | `50` | Jobs fetched before query filtering |
| `JOBS_CACHE_TTL_SECONDS` | `3600` | Cached job search TTL |
| `LLM_PROVIDER` | `auto` | `auto`, `ollama`, `openai_compatible`, or `disabled` |
| `LLM_PROVIDER_LABEL` | empty | Display name, e.g. `requesty` |
| `LLM_BASE_URL` | `https://router.requesty.ai/v1` | OpenAI-compatible base URL |
| `LLM_API_KEY` | empty | Cloud provider key; backend only |
| `LLM_MODEL` | `google/gemma-4-31b-it` | Cloud model ID |
| `LLM_JSON_MODE` | `false` | Send `response_format` when supported |
| `LLM_STATUS_CACHE_SECONDS` | `300` | Cache successful provider status |
| `LLM_DAILY_REQUEST_LIMIT` | `180` | Local per-process cloud generation cap; `0` disables |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Local Ollama server |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | Local model used for generation |
| `LLM_TIMEOUT_SECONDS` | `60` | Per-request LLM timeout |
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
  `PATCH /api/applications/{id}`, `POST /api/applications/{id}/approve`
- `POST /api/interviews`, `POST /api/interviews/{id}/evaluate`
- `GET /api/dashboard`, `GET /api/traces`

Errors use a consistent envelope:

```json
{
  "error": {"code": "job_not_found", "message": "Search for this job first."},
  "request_id": "..."
}
```

## Free deployment: Vercel + Render + Neon

This stack is intended for a non-commercial demo. Vercel Hobby is for personal,
non-commercial projects. Render Free web services sleep after 15 minutes of
inactivity and take about a minute to wake. Neon Free includes 1 GB of storage
and 100 CU-hours per project per month, and scales to zero after 5 minutes.

### 1. Neon Postgres

1. Create a Neon project and copy its pooled connection string.
2. Convert it to SQLAlchemy's psycopg form and require TLS:

   ```dotenv
   DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```

3. Keep this URL only in the Render backend environment. Do not use Render's
   free Postgres, which expires after 30 days.

### 2. Render backend

1. Create a Render Blueprint from the repository. `render.yaml` defines the
   free Python web service with root `backend`.
2. Set these secret environment variables in Render:
   - `DATABASE_URL` — the Neon URL above
   - `CORS_ORIGINS` — the final Vercel origin, with no trailing slash
   - `LLM_API_KEY` — a rotated backend-only key
3. Deploy, then verify:
   - `https://<render-service>/healthz`
   - `https://<render-service>/readyz`
4. Alembic migrations run automatically during FastAPI startup. The free
   backend has no persistent disk; do not switch it back to SQLite.

### 3. Vercel frontend

1. Import the repository and set the Root Directory to `frontend`.
2. Set `VITE_API_URL=https://<render-service>/api`.
3. Deploy. `frontend/vercel.json` uses the Vite build and `dist` output.
4. Add the final Vercel URL to Render's `CORS_ORIGINS` and redeploy the backend.
   Add preview domains only if preview deployments need API access.

### 4. Deployment checks

1. Open the Vercel URL after the Render service has been idle. Confirm the
   “waking the workspace” notice appears and the first request completes.
2. Upload a resume, search, draft, edit, approve, and edit the approved draft.
3. Confirm the public API and traces never expose provider, model, endpoint, or
   model-list details.
4. Confirm the workspace remains usable in deterministic fallback mode.

## Production notes

- Render's current Python 3.14 runtime works; pin a specific Python version in Docker/CI for reproducible builds.
- SQLite with WAL is fine for local development. Use Neon Postgres on Render
  because the free filesystem is ephemeral.
- Generate content with an LLM only behind a provider abstraction with a
  deterministic fallback; never fabricate resume facts.
- Keep cloud provider keys in the backend environment only. The app caps cloud
  generation at `LLM_DAILY_REQUEST_LIMIT` per backend process; use a shared counter
  before running multiple workers because Requesty's free tier is limited to 200
  requests per day.
- Export approved drafts and add email/calendar reminders next.
- See [docs/plan.md](docs/plan.md) for the full production roadmap.
