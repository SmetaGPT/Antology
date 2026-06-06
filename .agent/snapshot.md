<!-- generated: run npm run agent:sync -->
<!-- source: .agent/state.json -->
<!-- generatedAt: 2026-06-06T16:16:43.042Z -->

# Agent Startup

- Goal: Ship a production-ready full-stack landing page with a real lead flow.
- Phase: `sprint-5-ready`
- Default: `.agent/state.json` -> `.agent/snapshot.md`

## Now
- [`SPRINT-5`] Paper edition review flow (admin)
- Owner: `agent`
- Status: `active`
- Next: Implement paper request review actions, admin event logging, and approval or rejection email jobs.
- Areas: `admin`

## Next
- [`SPRINT-6`] Book upload admin flow (admin)

## Later
- [`SPRINT-7`] Anti-spam, privacy, and content readiness (quality)
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
