# Lean Production Roadmap

## Purpose

This roadmap defines the autonomous agent delivery plan for the Antology landing
project. The confirmed architecture is intentionally lean: a static landing page,
a small FastAPI backend, SQLite for up to roughly 1000 requests, file storage for
the electronic book, delayed email delivery, and a simple admin UI.

Default agent startup should still use `.agent/state.json` and
`.agent/snapshot.md`. Read this file only when planning or executing sprint work.

## Confirmed Business Flow

1. A visitor reads the landing page.
2. The visitor submits the request form and leaves contact details.
3. If electronic access is requested, the backend sends a download link to the
   submitted email after a configurable delay.
4. The electronic book is about 200 MB, so email must contain a download link,
   not the file itself.
5. If a printed edition is requested, the application creates an admin-reviewed
   paper request.
6. An administrator reviews paper requests and sends pickup information when a
   request is approved.
7. An administrator can view simple statistics and upload a new electronic book
   revision.

## Target Architecture

- Frontend: Vite/React static landing page.
- Backend: Python FastAPI monolith.
- Database: SQLite with WAL mode and backup discipline.
- Book storage: local persistent storage directory on the server.
- Downloads: tokenized download links.
- Email: SMTP or transactional email provider configured by environment.
- Worker: small Python process that sends due email jobs.
- Admin: simple FastAPI-served admin UI, not a separate SPA initially.
- HTTPS/proxy: Caddy, Nginx, or equivalent reverse proxy.

## Non-Goals For First Production Release

- PostgreSQL.
- Celery, Redis, or a distributed queue.
- Kubernetes or a complex orchestration stack.
- A full CRM.
- A separate React admin application.
- Sending the 200 MB book as an email attachment.

## Data Model

### `requests`

- `id`
- `first_name`
- `last_name`
- `organization`
- `position`
- `email`
- `phone`
- `purpose`
- `format`: `electronic`, `paper`, `both`
- `consent`
- `electronic_status`: `none`, `pending`, `sent`, `failed`
- `paper_status`: `none`, `review`, `approved`, `rejected`
- `created_at`
- `updated_at`

### `book_versions`

- `id`
- `title`
- `version_label`
- `file_path`
- `file_name`
- `file_size`
- `checksum`
- `is_active`
- `uploaded_at`

### `download_tokens`

- `id`
- `request_id`
- `book_version_id`
- `token_hash`
- `expires_at`
- `used_count`
- `last_used_at`
- `created_at`

### `email_jobs`

- `id`
- `request_id`
- `kind`: `electronic_link`, `paper_pickup`, `paper_rejected`
- `recipient_email`
- `subject`
- `body`
- `status`: `pending`, `sent`, `failed`
- `send_after`
- `attempt_count`
- `last_error`
- `sent_at`
- `created_at`

### `admin_users`

- `id`
- `email`
- `password_hash`
- `is_active`
- `created_at`

### `admin_events`

- `id`
- `admin_user_id`
- `event_type`
- `entity_type`
- `entity_id`
- `metadata_json`
- `created_at`

## Environment Contract

- `APP_ENV`: `development` or `production`
- `API_PREFIX`: default `/api`
- `CORS_ORIGINS`: comma-separated frontend origins
- `DATABASE_PATH`: SQLite database path
- `BOOK_STORAGE_DIR`: persistent directory for book files
- `DOWNLOAD_TOKEN_TTL_HOURS`: token lifetime
- `DELIVERY_DELAY_MINUTES`: delay before electronic link email
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `SECRET_KEY`

## Sprint Plan

### Sprint 0: Control Plane And Baseline

Goal: keep agents aligned and make the project reproducible locally.

Tasks:
- Keep `.agent/state.json` as the canonical active-state file.
- Keep detailed roadmaps and prompts under `docs/`.
- Add backend run commands to documentation.
- Ensure frontend and backend checks are executable.
- Verify `.venv`, SQLite files, uploads, and generated artifacts are ignored.

Acceptance:
- `npm run agent:validate` passes.
- `npm run typecheck` passes.
- `npm run build` passes.
- `backend\.venv\Scripts\python -m pytest backend\tests` passes.

### Sprint 1: Request Intake And Status Model

Goal: turn the current request endpoint into a durable request workflow.

Tasks:
- Expand SQLite schema for electronic and paper statuses.
- Add `updated_at` fields.
- Enable SQLite WAL mode.
- Remove repeated `init_database()` calls from request inserts where possible.
- Add repository/service functions for request creation.
- Calculate electronic delivery due time from `DELIVERY_DELAY_MINUTES`.
- Create initial `email_jobs` row for electronic or both formats.
- Put paper or both formats into `paper_status = review`.

Acceptance:
- Electronic request creates a request, token candidate, and email job.
- Paper request creates a reviewable request and no electronic email job.
- Both creates both flows.
- Tests cover all three formats.

### Sprint 2: Book Version Storage And Download Tokens

Goal: make the electronic book downloadable by secure link.

Tasks:
- Add `book_versions` table.
- Add `download_tokens` table.
- Add secure token generation and token hashing.
- Add active book lookup.
- Add download endpoint: `GET /download/{token}`.
- Stream or delegate the file download safely.
- Return 404/410 for invalid or expired tokens.
- Store token usage count and last-used timestamp.

Acceptance:
- Admin-seeded active book can be downloaded by valid token.
- Invalid token is rejected.
- Expired token is rejected.
- Download does not expose the real storage path.

### Sprint 3: Email Delivery Worker

Goal: send delayed book links reliably without a heavy queue stack.

Tasks:
- Add SMTP settings.
- Add email template for electronic link.
- Add worker entrypoint: `python -m app.worker`.
- Worker polls pending due jobs.
- Worker sends email and marks jobs as `sent`.
- Worker increments attempts and stores `last_error` on failure.
- Add max retry count.
- Add tests with mocked email sender.

Acceptance:
- Due electronic jobs are sent.
- Future jobs are ignored until due.
- Failed jobs keep error metadata.
- Worker can run locally without starting the frontend.

### Sprint 4: Admin Authentication And Dashboard

Goal: provide a minimal admin place to review requests and see system state.

Tasks:
- Add admin login.
- Store hashed admin password.
- Add session cookie or signed admin token.
- Add dashboard with counts:
  - total requests
  - electronic sent
  - electronic failed
  - paper review
  - paper approved
  - paper rejected
- Add request list with filters.
- Add request detail page.

Acceptance:
- Anonymous users cannot access admin pages.
- Admin can log in and log out.
- Dashboard counts match test fixtures.
- Admin can inspect submitted contact data.

### Sprint 5: Paper Edition Review Flow

Goal: support manual decisioning for printed edition requests.

Tasks:
- Add approve/reject actions for paper requests.
- Add pickup information field for approvals.
- Add rejection/admin note field.
- Add email templates for approval and rejection.
- Create email jobs when admin changes paper status.
- Add admin event logging.

Acceptance:
- Paper approval creates a pickup email job.
- Paper rejection creates a rejection email job.
- Admin action is recorded in `admin_events`.
- Request status transitions are validated.

### Sprint 6: Book Upload Admin Flow

Goal: let admin upload and activate a new electronic book revision.

Tasks:
- Add admin upload page.
- Validate uploaded file type and max size.
- Store file under `BOOK_STORAGE_DIR`.
- Calculate checksum and file size.
- Create `book_versions` record.
- Let admin mark one version as active.
- Show active version on dashboard.

Acceptance:
- Admin can upload a new PDF.
- Uploaded file is stored outside the repo.
- Only one book version is active.
- New electronic requests use the active version.

### Sprint 7: Anti-Spam, Privacy, And Content Readiness

Goal: reduce abuse and close basic legal/content blockers.

Tasks:
- Add honeypot field to frontend and backend.
- Add simple rate limit by IP/email.
- Add privacy policy route or static page.
- Replace placeholder legal/contact links.
- Add consent timestamp to stored request.
- Review wording for personal data handling.

Acceptance:
- Honeypot submissions are rejected or silently dropped.
- Repeated abuse is throttled.
- Form links point to real legal content.
- Stored requests include consent evidence.

### Sprint 8: Deployment And Operations

Goal: make the system deployable and maintainable.

Tasks:
- Add backend Dockerfile.
- Add production run command.
- Add docker-compose for local production-like run.
- Add persistent volume layout:
  - SQLite database
  - book storage
  - logs/backups
- Add backup script for SQLite and book files.
- Add reverse proxy example for `/api` and downloads.
- Add production env example.

Acceptance:
- Fresh deployment can run from documented commands.
- Database and books survive container restart.
- Backup command produces restorable artifacts.
- Healthcheck endpoint works behind proxy.

### Sprint 9: Release Hardening

Goal: close first-release quality gates.

Tasks:
- Add backend smoke tests for request, email job, token, and admin flows.
- Add frontend build/typecheck to CI or local release script.
- Add backend tests to release script.
- Review dependency audit and update safe versions.
- Add basic structured logging.
- Disable public docs/OpenAPI in production if required.

Acceptance:
- One command validates frontend, backend, and agent harness.
- No known high-risk release blockers remain.
- Admin can upload a book, receive requests, send links, and handle paper reviews.

## Agent Execution Rules

- Start with `.agent/snapshot.md`.
- Read this roadmap only when executing sprint work.
- One sprint should be completed and validated before starting the next.
- Each sprint must update `.agent/state.json` and regenerate `.agent/snapshot.md`.
- Do not add heavy infrastructure unless a sprint acceptance criterion requires it.
- Prefer small FastAPI modules over broad rewrites.
- Keep admin UI server-rendered until there is a concrete need for a separate SPA.

## Suggested Agent Prompts

### Sprint Execution Prompt

Use the current repository harness. Read `.agent/snapshot.md`, then read
`docs/roadmap-lean-production.md` only for the active sprint. Implement the sprint
acceptance criteria with minimal architecture. Run focused tests first, then the
full available validation set. Update `.agent/state.json` and regenerate
`.agent/snapshot.md` before finishing.

### Review Prompt

Review the completed sprint against `docs/roadmap-lean-production.md`. Focus on
bugs, missing acceptance criteria, data integrity risks, security/privacy issues,
and missing tests. Report findings first with file references.
