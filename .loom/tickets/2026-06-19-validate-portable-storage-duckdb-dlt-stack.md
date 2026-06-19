Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md, .loom/research/2026-06-19-portable-dlt-duckdb-storage-research.md

# Validate Portable Storage + DuckDB + dlt Stack

## Scope

Prove the storage/query/ingestion compatibility risks before broad refactors.

Validate:

- DuckDB can read local Delta tables with `delta_scan`.
- DuckDB extension setup is scriptable and compatible with project tests.
- dlt filesystem/S3-compatible configuration can represent local/MinIO/R2 profiles.
- delta-rs storage options needed for MinIO/R2 are understood and documented.
- R2 and MinIO credential conventions can be represented without committing secrets.

## Out of Scope

- Migrating production code paths.
- Rewriting bronze/silver/gold models.
- Requiring live R2 credentials in deterministic tests.
- Public deployment.

## Acceptance Criteria

- A validation script or tests prove DuckDB `delta_scan` over a fixture local Delta table.
- Evidence records the exact DuckDB extensions/secrets needed for local and object-store profiles.
- MinIO and R2 config shapes are documented with placeholders only.
- The ticket clearly states whether live R2 validation was run or skipped.
- `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` pass after any validation scaffolding.

## Progress and Notes

- Not started.

## Blockers

- Requires implementation approval.
