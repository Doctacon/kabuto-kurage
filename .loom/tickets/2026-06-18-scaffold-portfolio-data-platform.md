Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md

# Scaffold Portfolio Data Platform

## Scope

Create the initial repository scaffold for a portfolio-quality Python data platform.

Expected areas:

- Source package layout.
- Tests layout.
- `uv` or selected Python package manager setup.
- Formatting/linting/type-checking configuration.
- Environment variable conventions.
- `.gitignore` entries for secrets, local data, and generated artifacts.
- Initial README skeleton.
- Developer commands for install, test, lint, and Dagster startup.

## Out of Scope

- Real GitHub ingestion.
- Real Delta table design beyond placeholders needed for structure.
- Full documentation polish.

## Acceptance Criteria

- A new developer can install dependencies with documented commands.
- Tests can be run locally.
- Lint/type-check commands exist or are intentionally deferred with rationale.
- Secret and local-data paths are ignored by git.
- README explains the project goal and current milestone.

## Progress and Notes

- Not started.

## Blockers

- Depends on stack validation.
