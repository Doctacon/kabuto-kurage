Status: open
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

## Progress and Notes

- Not started.

## Blockers

- Requires stack validation ticket.
