Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Target: .loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md
Verdict: pass

# Storage Profiles and Secret Conventions Review

## Target

Review of the implementation for `.loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md`, including:

- `src/kabuto_kurage/paths.py`
- `tests/test_storage_profiles.py`
- `.env.example`
- `.gitignore`
- `docs/tenancy.md`
- `docs/local-iac.md`
- `docs/stack-validation.md`
- `.loom/evidence/2026-06-19-storage-profiles-secret-conventions-validation.md`

## Findings

### Pass: local compatibility preserved

Existing local path behavior remains intact for the default profile. Tests cover both default `.local/data/delta` behavior and `KABUTO_DATA_ROOT` override behavior. Existing tests across bronze/silver/gold/Dagster/export surfaces passed.

### Pass: profile resolution is centralized

`kabuto_kurage.paths` now owns active profile loading, validation, Delta root/table URI construction, and local path compatibility helpers. Object-store profiles have URI helpers instead of forcing non-local storage through `Path`.

### Pass: secret handling is explicit and redacted by default

Secret-bearing delta-rs and DuckDB configuration helpers default to placeholder/env-var names. Tests assert fake secret values do not appear in safe summaries, redacted options, or redacted SQL. Actual secret values are available only through explicit `include_secrets=True` calls for future engine-boundary use.

### Pass: docs/examples use placeholders only

`.env.example` and docs show variable names and placeholder patterns for MinIO and R2. They include Proton Pass-safe guidance and do not include real secrets, bucket names, or account IDs.

### Minor residual risk: future engine-boundary logging

Future tickets that call `delta_rs_storage_options(include_secrets=True)` or `duckdb_secret_sql(include_secrets=True)` must avoid logging returned dictionaries/SQL. This risk is documented in evidence and should be reiterated in later implementation tickets.

### Minor residual risk: no live object-store validation in this ticket

No live MinIO/R2 service was required or used. This matches the ticket scope. Later storage/IaC work should validate MinIO and optionally R2 when credentials are available.

## Verdict

Pass. The implementation satisfies this ticket's acceptance criteria without expanding into bronze ingestion migration or DuckDB query migration.

## Residual Risk

- Future code must avoid logging secret-bearing options returned with `include_secrets=True`.
- Live MinIO/R2 behavior remains to be validated in later tickets.
