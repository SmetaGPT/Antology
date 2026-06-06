<!-- generated: run npm run agent:sync -->
<!-- source: .agent/state.json -->
<!-- generatedAt: 2026-06-06T17:19:17.962Z -->

# Agent Startup

- Goal: Ship a production-ready full-stack landing page with a real lead flow.
- Phase: `release-blocked`
- Default: `.agent/state.json` -> `.agent/snapshot.md`

## Now
- [`REL-001`] Final content and legal approval (content)
- Owner: `agent`
- Status: `blocked`
- Next: Resolve final content, legal destinations, and approved media assets before release sign-off.
- Areas: `content`, `release`

## Next
- none

## Later
- none

## Blockers
- [`BLK-002`] Production content and legal assets are incomplete (high) -> Provide final contacts, legal targets, and approved media assets.

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
