Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-migrate-bronze-to-dlt-native-github-source.md, .loom/tickets/2026-06-19-query-gold-metrics-with-duckdb.md, .loom/tickets/2026-06-19-add-taskfile-developer-workflow.md

# Update Modernized Portfolio Docs

## Scope

Update portfolio-facing documentation after the modernized storage/ingestion/query/dev-workflow implementation lands.

Expected docs updates:

- README architecture narrative.
- `docs/architecture.md` diagrams and walkthrough.
- `docs/github-bronze-ingestion.md` for dlt-native source/resources/schema/state.
- `docs/stack-validation.md` for DuckDB/dlt/object-storage validation.
- `docs/export-api.md` for DuckDB-backed query layer if relevant.
- `docs/local-iac.md` for MinIO/storage profiles if relevant.
- Developer workflow docs for Taskfile.
- Secret handling guidance for Proton Pass/env vars.

## Out of Scope

- Implementing storage/query/ingestion code changes.
- Publishing public docs.
- Adding a dashboard.

## Acceptance Criteria

- Docs accurately reflect implemented storage profiles, dlt-native ingestion, DuckDB query layer, and Taskfile commands.
- Docs preserve public-Jellyfish inspiration boundaries and do not claim internals.
- Docs do not include real secrets, bucket names, account IDs, or tokens.
- Documentation tests are updated or added where appropriate.
- Full test/lint/typecheck validation passes.

## Progress and Notes

- Not started.

## Blockers

- Requires implementation tickets to finish first so docs describe reality.
