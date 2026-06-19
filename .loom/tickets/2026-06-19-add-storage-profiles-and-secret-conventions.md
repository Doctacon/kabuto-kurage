Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-validate-portable-storage-duckdb-dlt-stack.md

# Add Storage Profiles and Secret Conventions

## Scope

Add project configuration for portable storage profiles:

- `local`: local filesystem default for tests/dev.
- `minio`: open-source S3-compatible local object-store profile.
- `r2`: Cloudflare R2 remote S3-compatible profile for Chris's personal runs.

Expected work:

- Introduce storage profile config loading/validation.
- Centralize Delta table URI/path construction around the active profile.
- Represent required storage options for delta-rs and DuckDB without leaking secrets.
- Update `.env.example` and docs with placeholder-only MinIO/R2 variables.
- Add Proton Pass guidance: copy/export secrets into env vars, never commit or echo them.

## Out of Scope

- Hard-coding Chris's R2 bucket/account/secrets.
- Making R2 required for tests.
- Migrating bronze ingestion or DuckDB query execution; this ticket prepares storage config only.

## Acceptance Criteria

- Code can resolve Delta table locations for local, MinIO, and R2 profiles without embedding secrets.
- Tests cover profile validation and local deterministic path behavior.
- Docs show MinIO/R2 env var names and Proton Pass-safe export workflow.
- `.gitignore`/examples prevent accidental committed secrets.
- Full test/lint/typecheck validation passes.

## Current State

Done. Storage profile configuration conventions are implemented for local, MinIO, and R2.

Evidence: `.loom/evidence/2026-06-19-storage-profiles-secret-conventions-validation.md`.

Review: `.loom/reviews/2026-06-19-storage-profiles-secret-conventions-review.md`.

## Journal

- 2026-06-19: Set active and delegated storage profiles/secret conventions to worker.
- 2026-06-19: Added active storage profile resolution and Delta URI/path helpers in `src/kabuto_kurage/paths.py`.
- 2026-06-19: Added tests covering local default compatibility, data-root overrides, MinIO/R2 URI construction, redacted storage options/duckdb SQL, and invalid profile validation.
- 2026-06-19: Updated `.env.example`, `.gitignore`, and docs with MinIO/R2 env var names and Proton Pass-safe secret guidance.
- 2026-06-19: Validated with targeted storage tests, full pytest, ruff, and mypy.
- 2026-06-19: Recorded evidence/review and moved ticket to done.

## Progress and Notes

- Implemented `local`, `minio`, and `r2` profile conventions without migrating bronze ingestion or the DuckDB query layer.
- Existing local default behavior remains compatible with previous path tests and downstream tests.

## Results

Acceptance criteria satisfied:

- Code can resolve Delta table locations for local, MinIO, and R2 profiles without embedding secrets in table URIs.
- Tests cover profile validation and local deterministic path behavior.
- Docs show MinIO/R2 env var names and Proton Pass-safe export workflow.
- `.gitignore` and examples prevent accidental committed secrets.
- Full test/lint/typecheck validation passes.

## Blockers

None.
