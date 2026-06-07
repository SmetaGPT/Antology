<!-- generated: run npm run agent:sync -->
<!-- source: .agent/state.json -->
<!-- generatedAt: 2026-06-07T17:43:19.123Z -->

# Agent Startup

- Goal: Ship a production-ready full-stack landing page with a real lead flow.
- Phase: `release-blocked`
- Default: `.agent/state.json` -> `.agent/snapshot.md`

## Now
- [`REL-001`] Final content, legal, and launch-asset approval (content)
- Owner: `agent`
- Status: `blocked`
- Next: Resolve final content, legal destinations, approved media assets, and finish the final accessibility/content pass before release sign-off.
- Areas: `content`, `release`, `frontend`

## Next
- [`QA-001`] Final accessibility and content QA pass after approved assets land (frontend)

## Later
- none

## Blockers
- [`BLK-002`] Production content and legal assets are incomplete (high) -> Provide final contacts, legal targets, approved media assets, and production-approved wording for the launch surface.

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
