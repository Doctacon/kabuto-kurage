Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md

# Query Gold Metrics with DuckDB

## Scope

Replace the current Python in-memory export query implementation with DuckDB SQL over gold Delta tables.

Expected work:

- Add DuckDB dependency and a small query/session module if needed.
- Load/install required DuckDB extensions such as `delta` and object-store support where appropriate.
- Query `gold/github/pr_throughput_daily` and `gold/github/pr_cycle_time` through SQL.
- Express date/repository/merged filters, limits, offsets, and summary aggregation in SQL.
- Preserve REST/MCP response contracts and auth behavior.
- Keep tenant-scoped path validation before query execution.

## Out of Scope

- Changing REST endpoint paths or MCP tool names.
- Exposing raw bronze payloads.
- Cross-tenant query APIs.
- Performance tuning beyond correctness and local readability.

## Acceptance Criteria

- Query layer uses DuckDB SQL to read gold Delta tables.
- Existing REST/MCP tests pass or are adapted without changing public contracts.
- Tests prove tenant A cannot read tenant B data.
- Missing table and invalid filter errors remain predictable.
- DuckDB local Delta validation is covered by tests/evidence.
- Full test/lint/typecheck validation passes.

## Current State

Done. Export query layer now uses DuckDB SQL over tenant-scoped gold Delta tables while preserving REST/MCP contracts.

## Journal

- 2026-06-19: Set active and delegated DuckDB gold metrics query migration to worker.
- 2026-06-19: Replaced Python in-memory filtering/aggregation in `src/kabuto_kurage/queries/github_metrics.py` with DuckDB SQL and `delta_scan(?)` over tenant-scoped gold Delta tables.
- 2026-06-19: Preserved REST endpoint paths, MCP tool names, auth behavior, JSON response fields, and fail-closed tenant mismatch checks.
- 2026-06-19: Added/updated tests for DuckDB query backend visibility and docs coverage; existing query/REST/MCP tenant isolation tests pass.
- 2026-06-19: Recorded evidence in `.loom/evidence/2026-06-19-duckdb-gold-query-layer-validation.md` and review in `.loom/reviews/2026-06-19-duckdb-gold-query-layer-review.md`.
- 2026-06-19: Moved ticket to done after full validation passed.

## Progress and Notes

- 2026-06-19: Implemented DuckDB-backed query layer using storage-profile DuckDB setup and `duckdb_delta_table_uri(...)`.
- 2026-06-19: Throughput and cycle-time filters, ordering, limit, offset, and summary aggregation now execute in SQL.
- 2026-06-19: Updated `docs/export-api.md`, `docs/architecture.md`, and `docs/stack-validation.md` to describe DuckDB query execution.
- 2026-06-19: Validated with `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Results

Acceptance criteria satisfied:

- Query layer uses DuckDB SQL to read gold Delta tables.
- Existing REST/MCP tests pass without public contract changes.
- Tests prove tenant A cannot read tenant B data.
- Missing table and invalid filter errors remain predictable.
- DuckDB local Delta validation is covered by stack evidence and query tests.
- Full test/lint/typecheck validation passes.

## Blockers

None.
