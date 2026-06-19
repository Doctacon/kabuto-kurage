Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-migrate-bronze-to-dlt-native-github-source.md, .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md

# dlt-Native GitHub Bronze Source Validation

## What Was Observed

GitHub bronze ingestion was moved from a thin dlt REST-client wrapper toward explicit dlt source/resource/schema/state concepts while preserving the existing tenant-scoped Delta bronze contract.

Implementation observations:

- `src/kabuto_kurage/ingestion/github_bronze.py` now defines dlt source `github_bronze` with dlt resources `repositories` and `pull_requests`.
- Both resources carry dlt table hints: `replace` write disposition, `source_id` primary key, and bronze column hints.
- Resource iteration updates dlt source/resource state with tenant ID, ingestion run ID, fetched timestamp, row count, write disposition, and latest GitHub rate-limit snapshot.
- Each ingestion run writes local dlt inspection artifacts:
  - `.local/data/dlt/github/{tenant_id}/schema.json`
  - `.local/data/dlt/github/{tenant_id}/state.json`
- Existing tenant-scoped Delta bronze tables and raw `payload_json` auditability are preserved for downstream silver compatibility.

Validation commands run:

```bash
uv run pytest tests/test_github_bronze_ingestion.py -q
uv run pytest tests/test_github_silver_models.py tests/test_tenant_isolation.py -q
uv run ruff check .
uv run mypy src
uv run pytest
```

Observed output summary:

```text
uv run pytest tests/test_github_bronze_ingestion.py -q: 6 passed, 1 warning
uv run pytest tests/test_github_silver_models.py tests/test_tenant_isolation.py -q: 8 passed
uv run ruff check .: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
uv run pytest: 75 passed, 2 warnings in 4.24s
```

Warnings observed:

- FastAPI/Starlette deprecation warning from `fastapi.testclient` about future `httpx2` migration.
- dlt runtime warning that `XDG_DATA_HOME` is set while `~/.dlt` already exists; dlt selected `~/.dlt`.

Neither warning failed validation.

## Procedure

Deterministic tests use a local `requests` adapter mounted into dlt's REST client to simulate GitHub responses, pagination headers, and rate-limit headers without live network calls.

The focused ingestion tests verify dlt source/resource shape, dlt schema/state artifacts, pagination, rate-limit capture, raw payload retention, repeat-run overwrite behavior, and token non-leakage. Silver and tenant-isolation suites were run to verify downstream compatibility. The full suite was then run.

## What This Supports or Challenges

Supports the ticket acceptance criteria:

- GitHub ingestion uses explicit dlt source/resource/schema/state concepts.
- Tests prove pagination, rate-limit metadata, no token leakage, repeat-run behavior, and downstream tenant isolation.
- Silver model tests pass unchanged.
- Docs explain dlt schema/state artifacts and inspection commands.
- Full test/lint/typecheck validation passes.

## Limits

This evidence does not prove live GitHub extraction because deterministic tests use mocked responses. This ticket intentionally preserves the existing Delta bronze layout and does not migrate storage writes into dlt destinations. Query-layer DuckDB migration is out of scope for this ticket.
