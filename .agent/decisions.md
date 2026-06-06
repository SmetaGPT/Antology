# Decision Log

## Operating Rules

- The startup path is `state.json` plus `snapshot.md`.
- `roadmap.md`, `release.md`, and `decisions.md` are escalation docs.
- One blocker should be maintained once in `state.json`, then referenced elsewhere.

## Decision Log

### DEC-001

- Status: accepted
- Decision: use `.agent/state.json` as the canonical machine-readable source for
  current work, blockers, and startup bundle definitions.
- Why: it keeps the startup path compact and makes validation straightforward.

### DEC-002

- Status: accepted
- Decision: generate `.agent/snapshot.md` from `state.json`.
- Why: it avoids narrative drift between the human startup view and machine state.

### DEC-003

- Status: accepted
- Decision: the backend will be built in Python with FastAPI.
- Initial shape:
  - HTTP API under `backend/app`
  - `SQLite` persistence for local bootstrap
  - request-access endpoint as the first production path
- Why it matters: backend language and framework are now fixed, which unblocks API
  structure, validation, and local development flow.

### DEC-004

- Status: accepted
- Decision: token-efficient startup is now mode-based.
- Startup modes:
  - `local-fast-path` -> `snapshot-only`
  - `cross-module` -> `default`
  - `resume` -> `default`
  - `release` -> `release`
  - `architecture` -> `architecture`
- Why: agents should not read roadmap, release, or decisions docs unless the task
  actually requires them.

### DEC-005

- Status: accepted
- Decision: use a lean monolithic FastAPI backend for the first production
  release.
- Shape:
  - SQLite with persistent storage for up to roughly 1000 requests
  - local persistent book storage
  - tokenized download links for the electronic book
  - small email worker for delayed delivery
  - simple server-rendered admin UI
- Why: the business workflow is narrow and does not justify PostgreSQL, Celery,
  Redis, or a separate admin SPA for the first release.

### DEC-006

- Status: accepted
- Decision: delayed electronic-book delivery runs through a small polling worker
  in the same FastAPI codebase.
- Shape:
  - SMTP delivery through environment-configured credentials
  - absolute download links built from `PUBLIC_BASE_URL`
  - `email_jobs` stay in SQLite and are retried up to a configured cap
  - hard failures mark the request as `electronic_status = failed`
- Why: this keeps the release path operationally small while still giving the
  project a durable delayed-delivery flow and auditable retry metadata.

### DEC-007

- Status: accepted
- Decision: the first admin surface stays server-rendered inside the FastAPI
  app and uses a small signed cookie session.
- Shape:
  - bootstrap admin user seeded from environment
  - hashed password stored in `admin_users`
  - `/admin` dashboard and request detail pages rendered without a separate SPA
- Why: the admin workflow is still narrow, and a server-rendered panel keeps the
  operational footprint lower than introducing a second frontend application.
