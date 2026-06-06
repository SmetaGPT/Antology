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

### DEC-008

- Status: accepted
- Decision: paper-edition decisions are handled as state transitions on the
  existing request row, with follow-up email jobs and append-only admin events.
- Shape:
  - `paper_status` moves from `review` to `approved` or `rejected`
  - approval stores pickup information, rejection stores an admin note
  - admin actions enqueue `paper_pickup` or `paper_rejected` email jobs
  - each decision writes an `admin_events` audit row
- Why: the printed-edition flow is operationally small, but it still needs
  durable review state, traceability, and delayed outbound email handling.

### DEC-009

- Status: accepted
- Decision: book revision management stays in the same admin surface and stores
  PDF files in the configured server-side book storage directory.
- Shape:
  - PDF uploads are validated by content type, extension, and size cap
  - uploaded files are stored under `BOOK_STORAGE_DIR` with generated filenames
  - `book_versions` keeps checksum, size, and active flag
  - admins can activate a different version without re-uploading the file
- Why: the book is a core project asset, and a single lightweight admin flow is
  enough to manage versions without introducing object storage or a second app
  before the first production release.

### DEC-010

- Status: accepted
- Decision: the first production release uses lightweight anti-spam and privacy
  controls instead of an external abuse-prevention service.
- Shape:
  - honeypot submissions are silently accepted but not persisted
  - repeated submissions are rate-limited by email and IP inside SQLite-backed logic
  - requests now store consent timestamp and basic request metadata
  - legal links point to local static policy pages instead of placeholders
- Why: the landing flow is narrow, traffic is expected to stay modest, and these
  controls close the main release risks without introducing more infrastructure.

### DEC-011

- Status: accepted
- Decision: release hardening uses one repository-level validation command and
  production-safe FastAPI defaults.
- Shape:
  - `npm run release:check` runs agent harness validation, frontend typecheck,
    frontend build, and backend smoke tests
  - FastAPI public docs and OpenAPI endpoints are disabled by default in production
  - backend and worker emit structured JSON logs to stdout/stderr
  - dependency review uses `npm audit --omit=dev` for frontend production deps
    and `pip_audit` for backend Python deps
- Why: the first release needs one repeatable validation path and minimal
  operational hardening without adding CI-only complexity.
