Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-validate-portable-storage-duckdb-dlt-stack.md, .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md

# Portable Storage + DuckDB + dlt Stack Validation

## What Was Observed

Validation scaffolding was added for the first modernization child ticket.

Changed implementation/docs:

- `pyproject.toml` and `uv.lock` now include `duckdb>=1.4.0` as a runtime dependency.
- `tools/validate_stack.py` now validates DuckDB local Delta scanning with `INSTALL delta`, `LOAD delta`, and `delta_scan(?)` against a fixture Delta table written with `deltalake`.
- `tests/test_portable_storage_stack.py` proves the DuckDB validation helper returns the expected tenant-scoped row count and creates a real Delta transaction log.
- `docs/stack-validation.md` documents DuckDB local extension setup plus placeholder-only MinIO and Cloudflare R2 secret/config shapes.

Validation commands run:

```bash
uv add 'duckdb>=1.4.0'
uv run pytest tests/test_portable_storage_stack.py -q
uv run ruff check tests/test_portable_storage_stack.py tools/validate_stack.py
uv run mypy src
uv run python tools/validate_stack.py
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Observed output summary:

```text
uv run pytest tests/test_portable_storage_stack.py -q: 1 passed
uv run ruff check tests/test_portable_storage_stack.py tools/validate_stack.py: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
uv run python tools/validate_stack.py: delta passed, duckdb_delta passed, dagster passed, GitHub live auth skipped because no token was set
uv run pytest: 69 passed, 2 warnings in 4.12s
uv run ruff check .: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
```

Warnings observed during full pytest:

- FastAPI/Starlette deprecation warning from `fastapi.testclient` about future `httpx2` behavior.
- dlt runtime warning that `XDG_DATA_HOME` is set while `~/.dlt` already exists; dlt selected `~/.dlt`.

Neither warning failed validation.

## Procedure

The deterministic DuckDB proof writes a local Delta table with two `tenant_alpha` rows, installs/loads DuckDB's `delta` extension, and queries it with:

```sql
SELECT tenant_id, count(*) AS row_count
FROM delta_scan(?)
GROUP BY tenant_id
```

`docs/stack-validation.md` records exact extension/secret shapes for:

- local Delta: `INSTALL delta; LOAD delta; SELECT * FROM delta_scan('/path/to/table');`
- MinIO: `INSTALL httpfs; LOAD httpfs; INSTALL delta; LOAD delta; CREATE SECRET ... TYPE s3 ... ENDPOINT 'localhost:9000' ... URL_STYLE 'path' ... USE_SSL false`.
- R2: `INSTALL httpfs; LOAD httpfs; INSTALL delta; LOAD delta; CREATE SECRET ... TYPE r2 ... KEY_ID ... SECRET ... ACCOUNT_ID ...`.

The documented MinIO/R2 values are placeholders only. No real account IDs, bucket names, access keys, or secrets were added.

## What This Supports or Challenges

Supports acceptance criteria for `.loom/tickets/2026-06-19-validate-portable-storage-duckdb-dlt-stack.md`:

- DuckDB can scan a local Delta table through `delta_scan`.
- Extension requirements for local/object-store profiles are documented.
- MinIO and R2 config shapes are represented without secrets.
- R2 live validation is explicitly optional and was not run.
- Full tests, lint, and typecheck pass.

## Limits

Live MinIO and live R2 validation were not run in this ticket. That is intentional: this ticket validates local deterministic DuckDB/Delta behavior and records safe object-store config shapes. Later storage-profile tickets should validate MinIO with local services and R2 only when credentials are available through ignored environment/config.
