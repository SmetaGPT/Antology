# Deployment And Operations

## Purpose

This document defines the lean production runtime for the Antology landing
system. It is intentionally small: one static web container, one FastAPI API
container, one worker container, SQLite on a persistent volume, and a backup
path for the database and uploaded book files.

## Runtime Layout

- `web`: serves the built frontend and reverse-proxies `/api`, `/download`,
  `/admin`, and `/healthz` to the backend.
- `backend`: handles request intake, admin pages, downloads, and healthchecks.
- `worker`: processes due email jobs.
- `mailhog`: local SMTP sink for production-like testing on a developer machine.
- host runtime data directory, default `./runtime/data`:
  - `leads.db`
  - `books/*`
  - `backups/*`
- host runtime log directory, default `./runtime/logs`:
  - reserved for runtime log files if file-based logging is added later
  - current default runtime logging still goes to container stdout/stderr

## Files

- `backend/Dockerfile`: backend production image
- `Dockerfile.web`: frontend build + static web image
- `docker-compose.yml`: local production-like orchestration
- `deploy/Caddyfile`: reverse proxy and static file setup
- `.env.production.example`: production env contract example
- `scripts/ops/backup_runtime.py`: restorable runtime backup archive builder
- `scripts/release/check.mjs`: one-command release validation entrypoint

## Release Validation

Run the full pre-release validation set with one command:

```powershell
npm run release:check
```

The command validates:

- agent harness state and snapshot generation
- frontend typecheck
- frontend production build
- backend smoke tests in `backend/tests`

## Fresh Local Production-Like Run

1. Copy `.env.production.example` to `.env.production` and replace secrets,
   SMTP credentials, admin credentials, and public domain values.
2. Load those values into your shell, or convert them to the environment format
   expected by your deployment platform.
3. The default bind mounts write runtime state into `./runtime/data` and
  `./runtime/logs`. Override `RUNTIME_DATA_DIR` and `RUNTIME_LOG_DIR` if your
  deployment host needs different persistent paths.
4. Build and start the stack:

```powershell
docker compose --env-file .env.production up -d --build
```

If port `8080` is already occupied on the host, set `WEB_PORT` in
`.env.production` to another free port before starting the stack.

5. Open the frontend at `http://localhost:8080`
6. Open admin at `http://localhost:8080/admin`
7. Optional local email inspection UI: `http://localhost:8025`
8. Healthcheck through the proxy:

```powershell
curl http://localhost:8080/healthz
```

## Reverse Proxy Contract

The proxy currently routes:

- `/api/*` -> FastAPI backend
- `/download/*` -> FastAPI backend
- `/admin*` -> FastAPI backend
- `/healthz` -> FastAPI backend
- everything else -> static frontend build

This contract is implemented in `deploy/Caddyfile` and can be translated to
Nginx or another proxy later without changing application code.

## Backup Command

Use the backup script against the bind-mounted runtime paths:

```powershell
python scripts/ops/backup_runtime.py --database runtime/data/leads.db --books runtime/data/books --output runtime/data/backups
```

The script creates a ZIP archive containing:

- the SQLite database
- all uploaded book files
- `manifest.json` with archive metadata

## Restore Outline

1. Stop write traffic to the backend and worker.
2. Unpack the selected backup archive.
3. Restore `database/leads.db` to `runtime/data/leads.db` or your configured
  `RUNTIME_DATA_DIR` database path.
4. Restore `books/*` to `runtime/data/books` or your configured
  `RUNTIME_DATA_DIR` books path.
5. Start backend and worker again.

## Deployment Notes

- Use `PUBLIC_BASE_URL` with the real public domain so email links are correct.
- `EXPOSE_API_DOCS=false` keeps `/docs`, `/redoc`, and `/openapi.json` closed in production by default.
- Keep `SECRET_KEY`, `ADMIN_PASSWORD`, and SMTP credentials out of git.
- Persist the SQLite database and book storage through `RUNTIME_DATA_DIR` so
  backups can run from the host without copying Docker named volumes.
- Run the backend behind a proxy so `--proxy-headers` in the Docker command is meaningful.
- Backend and worker now emit structured JSON logs to stdout/stderr for container-friendly collection.
- SQLite is still acceptable for this release target because expected request
  volume remains modest.

## Known Remaining Ops Work

- No automated restore verification yet.
- No structured log shipping yet.
- No scheduler for periodic backups yet.
- No TLS automation in this local compose file; production TLS should be handled
  by the real public proxy or load balancer.
