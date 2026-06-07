# Production Roadmap

## Purpose

This document is the escalation view for what remains after the startup bundle.
Use it for delivery planning, blockers, and release sequencing. Do not use it as
the default startup file.

Detailed sprint roadmap:
- `docs/roadmap-lean-production.md`

## Current Phase

- Phase: `release-blocked`
- Immediate objective: close the remaining launch blockers on content, legal
  destinations, approved assets, and final QA while keeping the validated lean
  production stack ready to ship.

## Workstreams

### Frontend Track

- `FRONT-001`: replace placeholder content, dead links, and prototype-only UX.
- `SEO-001`: finish metadata, social previews, robots, sitemap, and structured data.
- `QA-001`: add focused accessibility and performance checks.

Exit criteria:
- Real content and legal destinations are present.
- Approved media assets and share previews are present.
- SEO defaults and obvious accessibility issues are closed.

### Backend Track

- `BACK-001`: implement the request-access backend path.
- Runtime choice: Python `FastAPI` service.
- Initial persistence choice: local `SQLite` for development bootstrap.
- Current status:
- request intake and status workflow is live
- tokenized download endpoint is live
- delayed email worker is live
- admin authentication and dashboard are live
- paper-review actions, audit events, and follow-up email jobs are live
- book upload and active-version management are live
- anti-spam, consent evidence, and local legal pages are live
- deployment/runtime layout, backups, and release validation are live

Exit criteria:
- A real endpoint exists.
- Submissions are validated and stored.
- The frontend reflects success and failure states.
- Release validation stays green.

### Ops Track

- `OPS-001`: choose the production hosting/runtime model.
- Define environment variables and secret handling.
- Decide on logging, monitoring, and deployment flow.
- Decide how the Python API is deployed next to the frontend.

Exit criteria:
- Deployment target is explicit.
- Environment contract is documented.
- Release gates can be validated against a real target.

Current status:
- compose-based local production-like runtime is documented
- reverse proxy contract is documented
- persistent SQLite/book storage and backup flow are documented
- one-command release validation is live

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

## Near-Term Sequence

1. Keep the harness as the canonical control layer.
2. Remove production blockers in the frontend/content slice.
3. Land approved media/share assets and final legal/contact destinations.
4. Run the focused accessibility/content QA pass.
5. Re-run release validation against the release candidate content set.
