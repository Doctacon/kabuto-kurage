Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/specs/mini-engineering-intelligence-platform.md, .loom/decisions/initial-portfolio-architecture.md

# Validate Delta + Dagster + GitHub Stack

## Scope

Resolve the highest-risk technical choices before broad implementation.

This ticket should determine the concrete local stack for:

- Python package/runtime management.
- GitHub API client approach.
- Delta Lake read/write library.
- Dagster integration pattern.
- Local object/filesystem storage for Delta tables.
- Test strategy for deterministic fixtures alongside real GitHub API runs.

## Out of Scope

- Building the full ingestion pipeline.
- Implementing all Dagster assets.
- Creating production deployment infrastructure.

## Acceptance Criteria

- A short architecture note or ticket progress entry names the selected libraries and why they were chosen.
- A minimal proof exists that Python can write and read a local Delta table.
- A minimal proof exists that GitHub API access works with a token, or the expected setup failure is clearly documented.
- A minimal proof exists that Dagster can materialize a toy asset touching the selected storage approach.
- Risks and fallback options are recorded.

## Progress and Notes

- Not started.

## Blockers

- Requires implementation approval before execution.
