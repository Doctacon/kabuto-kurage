Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md

# Add Taskfile Developer Workflow

## Scope

Add `Taskfile.yml` as the primary user-facing command runner for common local workflows.

Expected tasks should cover:

- setup/sync;
- test/lint/typecheck/validate;
- Dagster dev server;
- GitHub ingestion for a tenant;
- silver and gold materialization for a tenant;
- observability CLI;
- REST API server;
- MCP server;
- optional storage-profile helpers where useful.

Existing Python scripts may remain as implementation entrypoints. Taskfile should make the normal workflow easier to discover and run.

## Out of Scope

- Removing Python scripts.
- Installing Task automatically on every platform.
- Building a custom CLI framework.

## Acceptance Criteria

- `Taskfile.yml` exists with documented common tasks.
- README/development docs teach Taskfile as the primary workflow.
- Tasks avoid echoing secret values.
- Validation tasks wrap `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- At least one task supports tenant parameterization, e.g. `task ingest tenant=sandbox`.
- Full test/lint/typecheck validation passes.

## Progress and Notes

- Not started.

## Blockers

- Can proceed after implementation approval. Some task names may be adjusted after storage-profile work lands.
