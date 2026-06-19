Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md, .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md

# Storage Profiles and Secret Conventions Validation

## What Was Observed

Implemented storage profile configuration conventions for local filesystem, MinIO, and Cloudflare R2 without migrating bronze ingestion or the query layer.

Changed implementation/docs:

- `src/kabuto_kurage/paths.py` now defines `DeltaStorageProfile`, `StorageConfigError`, active profile loading via `KABUTO_STORAGE_PROFILE`, Delta URI construction for `local`, `minio`, and `r2`, and safe representations of delta-rs storage options and DuckDB secret SQL.
- Existing local helpers such as `data_root()`, `delta_root()`, `tenant_delta_root()`, and `delta_table_path()` preserve local default behavior.
- New URI helpers such as `delta_root_uri()`, `tenant_delta_root_uri()`, `delta_table_uri()`, and `duckdb_delta_table_uri()` centralize active-profile table location construction.
- `.env.example` now includes placeholder-only `KABUTO_STORAGE_PROFILE`, `KABUTO_STORAGE_PREFIX`, `KABUTO_MINIO_*`, and `KABUTO_R2_*` settings.
- `.gitignore` now ignores `.dlt/` and `config/storage.local.yaml` in addition to existing local env/secrets paths.
- `docs/tenancy.md`, `docs/local-iac.md`, and `docs/stack-validation.md` document profile env vars and Proton Pass-safe secret handling.
- `tests/test_storage_profiles.py` covers local default compatibility, `KABUTO_DATA_ROOT` overrides, MinIO URI/options representation, R2 URI/options representation, invalid profile validation, missing bucket validation, and invalid prefix validation.

Validation commands run:

```bash
uv run pytest tests/test_storage_profiles.py -q
uv run ruff check src/kabuto_kurage/paths.py tests/test_storage_profiles.py
uv run mypy src
uv run pytest
uv run ruff check .
uv run mypy src
```

Observed output summary:

```text
uv run pytest tests/test_storage_profiles.py -q: 5 passed
uv run ruff check src/kabuto_kurage/paths.py tests/test_storage_profiles.py: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
uv run pytest: 74 passed, 2 warnings in 4.71s
uv run ruff check .: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
```

Warnings observed during full pytest:

- FastAPI/Starlette deprecation warning from `fastapi.testclient` about future `httpx2` behavior.
- dlt runtime warning that `XDG_DATA_HOME` is set while `~/.dlt` already exists; dlt selected `~/.dlt`.

Neither warning failed validation.

## Procedure

Deterministic tests use environment-variable monkeypatching only. They do not require live MinIO or R2 services and do not use real credentials. Object-store secret values in tests are fake and are asserted not to appear in safe summaries, redacted storage options, or redacted DuckDB SQL.

## What This Supports or Challenges

Supports acceptance criteria for `.loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md`:

- Code can resolve Delta table locations for local, MinIO, and R2 profiles.
- Profile validation and local deterministic path behavior are covered by tests.
- Docs and `.env.example` show MinIO/R2 env var names and Proton Pass-safe workflow.
- `.gitignore` and examples prevent accidental committed secrets.
- Existing local default behavior remains compatible.
- Full tests, lint, and typecheck pass.

## Limits

This ticket intentionally does not migrate dlt bronze ingestion, does not migrate REST/MCP queries to DuckDB, and does not require live R2 or MinIO validation. Secret-bearing options can be requested only when explicitly passing `include_secrets=True`; later engine-boundary code must avoid logging those returned dictionaries.
