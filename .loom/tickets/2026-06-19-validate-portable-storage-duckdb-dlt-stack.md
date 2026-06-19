Status: done
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

## Current State

Done. Portable storage/query stack validation scaffolding is implemented and validated.

Evidence: `.loom/evidence/2026-06-19-portable-storage-duckdb-dlt-stack-validation.md`.

Review: `.loom/reviews/2026-06-19-portable-storage-duckdb-dlt-stack-review.md`.

Live R2 validation was **not run** in this ticket. It was intentionally skipped because deterministic validation must not require live R2 credentials. Placeholder-only MinIO/R2 config and secret shapes are documented in `docs/stack-validation.md`.

## Journal

- 2026-06-19: Set active and delegated stack validation to worker.
- 2026-06-19: Added DuckDB runtime dependency.
- 2026-06-19: Extended `tools/validate_stack.py` to prove DuckDB `delta_scan(?)` over a local fixture Delta table.
- 2026-06-19: Added `tests/test_portable_storage_stack.py` to cover the DuckDB/Delta validation helper.
- 2026-06-19: Updated `docs/stack-validation.md` with DuckDB extension requirements and placeholder-only MinIO/R2 secret/config shapes.
- 2026-06-19: Ran focused and full validation: `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` passed.
- 2026-06-19: Recorded evidence and review; moved ticket to done.

## Progress and Notes

- DuckDB local Delta validation now uses `INSTALL delta`, `LOAD delta`, and `delta_scan(?)`.
- MinIO docs use DuckDB `TYPE s3` secret shape with placeholder access key/secret, endpoint, bucket, path-style URL, and non-SSL local settings.
- R2 docs use DuckDB `TYPE r2` secret shape with placeholder key ID, secret, account ID, and bucket.
- delta-rs object-store write option notes include `aws_conditional_put=etag` for MinIO/R2.

## Results

Acceptance criteria satisfied:

- A validation script and test prove DuckDB `delta_scan` over a fixture local Delta table.
- Evidence records DuckDB extensions/secrets needed for local and object-store profiles.
- MinIO and R2 config shapes are documented with placeholders only.
- Ticket clearly states live R2 validation was skipped/not run.
- Full `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` validation passed.

## Blockers

None.
