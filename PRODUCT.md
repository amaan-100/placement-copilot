# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Students and early-career job seekers navigating placement season. They use the product alone, often between classes or while applying from a laptop, and need to move from a resume to a shortlist, tailored application, and interview practice without losing control of what gets sent.

## Product Purpose

Placement Co-pilot is an approval-gated, multi-agent placement assistant. It reads a resume, finds relevant roles, drafts application material, and runs interview practice. Success means a student can complete the full loop in one sitting, understand what each agent did, and trust that nothing was submitted without explicit approval.

## Positioning

The product combines AI-assisted, resume-grounded generation with a server-enforced approval gate and an inspectable agent trace. A generic chatbot or job board cannot truthfully claim the same combination of grounded drafts, deterministic fallback, and human control.

## Operating Context

Students work in a browser with a text-based PDF resume. They search live job listings, draft applications one role at a time, edit and approve each draft, practice interview answers, and inspect recent agent activity. AI generation is optional, provider details stay server-side, and deterministic fallback keeps the workflow usable when AI is unavailable.

## Capabilities and Constraints

- PDF resume upload, text extraction, grounded skills, and an optional AI summary.
- Live job search through Jobicy with relevance filtering, caching, and a mock fallback.
- Tailored resumes and cover notes, with invented claims rejected by a grounding guard.
- Server-enforced approval before an application is marked approved; no automatic submission.
- Single-question interview practice with rubric-based feedback and score.
- Anonymous, session-scoped workspaces with no user accounts.
- Agent traces expose latency, AI/fallback state, and tool actions without revealing provider details.
- Generation uses a server-side AI integration; provider and model configuration stay out of consumer responses and UI.
- Interview practice is one question at a time, not a multi-turn state machine.
- Generated content is not yet fact-cited or user-editable.
- No Docker, CI, or seeded demo script is set up yet.

## Brand Commitments

The product name is Placement Co-pilot. The voice is clear, calm, and direct: it explains what happened and what the student should do next without hype or false certainty. The approval gate and visible agent trace are product commitments, not optional decoration.

## Evidence on Hand

- Real working flows for resume upload, live job search, application drafting, approval, and interview practice.
- AI-assisted generation with deterministic fallback and sanitized agent traces.
- Mock job data at `backend/data/mock_jobs.json` for offline use.
- No real student testimonials, customer logos, benchmarks, or placement statistics exist. Future work must not fabricate them.

## Product Principles

1. Keep the student in control of every consequential action.
2. Show the work: make agent activity, AI-assisted versus fallback state, and tool actions visible.
3. Ground every generated claim in the resume and reject what cannot be supported.
4. Make the next step obvious, even when the workspace is empty.
5. Stay useful when the network or AI service is unavailable.

## Accessibility & Inclusion

The interface is keyboard navigable, uses semantic landmarks and form labels, moves focus into dialogs, and respects reduced-motion preferences. No formal WCAG conformance level has been confirmed.
