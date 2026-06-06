# Production Roadmap

## Purpose

This document is the escalation view for what remains after the startup bundle.
Use it for delivery planning, blockers, and release sequencing. Do not use it as
the default startup file.

Detailed sprint roadmap:
- `docs/roadmap-lean-production.md`

## Current Phase

- Phase: `lean-production-sprints`
- Immediate objective: convert the prototype landing page into a production-ready
  lean full-stack system for requests, delayed book-link delivery, paper-edition
  review, and simple administration.

## Workstreams

### Frontend Track

- `FRONT-001`: replace placeholder content, dead links, and prototype-only UX.
- `SEO-001`: finish metadata, social previews, robots, sitemap, and structured data.
- `QA-001`: add focused accessibility and performance checks.

Exit criteria:
- Real content and legal destinations are present.
- Image rendering works without forced placeholders.
- SEO defaults and obvious accessibility issues are closed.

### Backend Track

- `BACK-001`: implement the request-access backend path.
- Runtime choice: Python `FastAPI` service.
- Initial persistence choice: local `SQLite` for development bootstrap.
- Current baseline:
- request intake and status workflow is live
- tokenized download endpoint is live
- delayed email worker is live
- admin authentication and dashboard are live
- paper-review actions, audit events, and follow-up email jobs are live
- book upload and active-version management are live
- anti-spam, consent evidence, and local legal pages are live
- Next work should support deployment, persistent runtime layout, and backups.

Exit criteria:
- A real endpoint exists.
- Submissions are validated and stored.
- The frontend reflects success and failure states.

### Ops Track

- `OPS-001`: choose the production hosting/runtime model.
- Define environment variables and secret handling.
- Decide on logging, monitoring, and deployment flow.
- Decide how the Python API is deployed next to the frontend.

Exit criteria:
- Deployment target is explicit.
- Environment contract is documented.
- Release gates can be validated against a real target.

### Content and Legal Track

- `LEGAL-001`: finalize privacy and consent language.
- Replace placeholder contact details and legal links.
- Add approved media assets and sharing previews.

Exit criteria:
- Footer and form link to real legal destinations.
- Contacts and brand assets are production-approved.

## Active Blockers

### BLK-002

- Title: Production content and legal assets are incomplete
- Effect: blocks release readiness even if engineering work lands
- Next action: provide final legal links, contacts, and approved media

### BLK-OPS

- Title: Python backend deploy target is undefined
- Effect: blocks final environment and release decisions
- Next action: choose hosting/runtime and define the environment contract

## Near-Term Sequence

1. Keep the harness as the canonical control layer.
2. Remove production blockers in the frontend/content slice.
3. Implement the Python form backend and its local persistence path.
4. Lock the deployment contract for the Python API.
5. Run release validation against the chosen target.
