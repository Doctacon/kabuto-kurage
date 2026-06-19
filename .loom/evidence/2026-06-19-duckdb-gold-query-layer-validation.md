Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-query-gold-metrics-with-duckdb.md, .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md

# DuckDB Gold Metrics Query Layer Validation

## What Was Observed

The export query layer was migrated from Python in-memory filtering over Delta rows to DuckDB SQL over tenant-scoped gold Delta tables.

Changed implementation/docs/tests:

- `src/kabuto_kurage/queries/github_metrics.py` now opens an in-memory DuckDB connection, applies active storage-profile DuckDB extension/secret setup, and queries gold Delta tables with `delta_scan(?)`.
- PR throughput, PR cycle time, and GitHub metrics summary filtering/ordering/pagination/aggregation are expressed in SQL.
- The query layer validates tenant IDs before constructing table URIs and scans only tenant-scoped gold table URIs from `duckdb_delta_table_uri(...)`.
- Mismatched tenant rows inside a tenant path still fail closed with the existing predictable error shape.
- REST endpoint paths and MCP tool names were not changed.
- `tests/test_export_github_metrics.py` now asserts the query backend reports DuckDB + `delta_scan` for the local storage profile.
- `docs/export-api.md`, `docs/architecture.md`, and `docs/stack-validation.md` now describe the DuckDB-backed query layer.

Validation commands run:

```bash
uv run pytest tests/test_export_github_metrics.py tests/test_export_rest_api.py tests/test_export_mcp_wrapper.py tests/test_export_api_docs.py -q
uv run ruff check src/kabuto_kurage/queries/github_metrics.py tests/test_export_github_metrics.py tests/test_export_api_docs.py
uv run mypy src
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Observed output summary:

```text
Targeted export/API/MCP/docs tests: 23 passed, 1 warning
Full pytest: 76 passed, 2 warnings in 5.19s
ruff: All checks passed!
mypy: Success: no issues found in 18 source files
git status --short: only expected unstaged modifications/new Loom evidence/review files
```

Warnings observed during full pytest:

- FastAPI/Starlette deprecation warning from `fastapi.testclient` about future `httpx2` behavior.
- dlt runtime warning that `XDG_DATA_HOME` is set while `~/.dlt` already exists; dlt selected `~/.dlt`.

Neither warning failed validation.

## Procedure

Deterministic tests write fixture-backed local Delta gold tables with `deltalake`, then exercise the query layer, REST API, and MCP wrapper against those tables. The DuckDB query layer installs/loads the configured Delta extension through the local storage profile and queries the fixture tables with `delta_scan(?)`.

## What This Supports or Challenges

Supports the ticket acceptance criteria:

- Query layer uses DuckDB SQL to read gold Delta tables.
- REST/MCP tests pass without endpoint/tool contract changes.
- Tenant isolation remains tested for query-layer, REST, MCP, and broader bronze/silver/gold behavior.
- Missing table and invalid filter errors remain predictable.
- DuckDB local Delta behavior is covered by existing portable stack validation and the new query backend test.

## Limits

This evidence validates the local filesystem storage profile. MinIO/R2 DuckDB secret shapes are centralized through storage profiles and documented, but live MinIO/R2 scans were not run in this ticket. Those require local object-store services or remote credentials supplied through ignored environment/config.
