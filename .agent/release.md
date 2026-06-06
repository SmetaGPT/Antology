# Release Status

## Verdict

- Current verdict: `not ready`
- Reason: the project is still a prototype with no real backend submission path,
  incomplete legal/content assets, and no deployment target for the Python API.

## Release Gates

| Gate | Status | Notes |
| --- | --- | --- |
| Frontend content integrity | blocked | Placeholder contacts and dead legal links remain. |
| Backend submission flow | in progress | Python backend bootstrap is being added, but the frontend is not wired yet. |
| SEO baseline | blocked | Vite defaults and missing share/search assets remain. |
| Accessibility baseline | blocked | Form semantics and interaction polish still need work. |
| Environment/deploy model | blocked | No production target is selected yet for the Python API. |
| Monitoring/observability | blocked | No runtime logging or failure path has been chosen. |

## Required For First Production Release

- Final content, contacts, and legal destinations.
- Working form backend with validation and persistence.
- Clear hosting/runtime decision and environment setup.
- Focused release checks for build, lint, typecheck, and core flow behavior.

## Escalate Here When

- A task asks whether the project can ship.
- A task changes release readiness or production gates.
- The team needs the current release verdict.
