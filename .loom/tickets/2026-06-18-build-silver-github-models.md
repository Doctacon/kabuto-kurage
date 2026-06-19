Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md

# Build Silver GitHub Models

## Scope

Transform raw GitHub bronze data into stable silver Delta tables for analytics.

Initial modeled entities:

- Repositories.
- Pull requests.
- Optional: users/authors if needed for metrics.

Expected behavior:

- Preserve tenant identity.
- Extract stable typed columns from raw payloads.
- Keep source IDs and URLs for traceability.
- Handle nulls and missing fields gracefully.
- Document how schema evolution would be handled when GitHub payloads change.

## Out of Scope

- Gold metrics.
- Full dimensional model for every GitHub entity.
- Jira or CI/CD models.

## Acceptance Criteria

- Silver tables are materialized from bronze data.
- Tests cover transformation of representative PR/repository fixtures.
- Silver model documentation includes table columns and intended use.
- A schema-evolution note explains what happens when new GitHub fields appear.

## Progress and Notes

- Not started.

## Blockers

- Requires bronze GitHub ingestion.
