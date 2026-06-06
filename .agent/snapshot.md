<!-- generated: run npm run agent:sync -->
<!-- source: .agent/state.json -->
<!-- generatedAt: 2026-06-06T16:24:11.475Z -->

# Agent Startup

- Goal: Ship a production-ready full-stack landing page with a real lead flow.
- Phase: `sprint-6-ready`
- Default: `.agent/state.json` -> `.agent/snapshot.md`

## Now
- [`SPRINT-6`] Book upload admin flow (admin)
- Owner: `agent`
- Status: `active`
- Next: Implement book upload and active-version management inside the admin flow.
- Areas: `admin`

## Next
- [`SPRINT-7`] Anti-spam, privacy, and content readiness (quality)

## Later
- [`SPRINT-8`] Deployment and operations (ops)
- [`SPRINT-9`] Release hardening (quality)

## Blockers
- [`BLK-002`] Production content and legal assets are incomplete (high) -> Provide final contacts, legal targets, and approved media assets.
- [`BLK-OPS`] Python backend deploy target is undefined (medium) -> Choose the hosting/runtime model, env contract, and secret handling for the Python API.

## Canonical
- Now: `.agent/state.json`
- Remaining: `docs/roadmap-lean-production.md`
- Release: `.agent/release.md`
- Decisions: `.agent/decisions.md`

## Paths
- `local-fast-path` -> `snapshot-only`
- `cross-module` -> `default`
- `resume` -> `default`
- `release` -> `release`
- `architecture` -> `architecture`
