Status: done
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

## Current State

Done. `Taskfile.yml` is now the primary user-facing workflow for common local development commands while Python scripts remain available as implementation entrypoints.

Evidence: `.loom/evidence/2026-06-19-taskfile-developer-workflow-validation.md`.

Review: `.loom/reviews/2026-06-19-taskfile-developer-workflow-review.md`.

## Journal

- 2026-06-19: Set active and delegated Taskfile developer workflow to worker.
- 2026-06-19: Added `Taskfile.yml` with setup/sync, test, lint, typecheck, validate, validate-stack, Dagster, materialize, ingest, silver, gold, observe, API, and MCP tasks.
- 2026-06-19: Updated README and `docs/development.md` to teach Taskfile as the primary workflow and document safe Proton Pass/env-var secret handling.
- 2026-06-19: Added `tests/test_taskfile_workflow.py` covering required tasks, validation commands, tenant parameterization, no common secret echo commands, docs coverage, and script preservation.
- 2026-06-19: Validated with `uv run pytest tests/test_taskfile_workflow.py -q`, `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- 2026-06-19: Recorded evidence and review, then moved ticket to done.

## Progress and Notes

- 2026-06-19: Added Taskfile as the documented primary local workflow without removing existing Python scripts.
- 2026-06-19: Full validation passed: 81 tests, Ruff, and mypy.

## Results

Acceptance criteria satisfied:

- `Taskfile.yml` exists with documented common tasks.
- README/development docs teach Taskfile as the primary workflow.
- Tasks avoid echoing secret values.
- Validation task wraps `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- Tenant parameterization is supported for ingestion, silver, gold, observation, and materialization.
- Existing Python scripts remain available.
- Full test/lint/typecheck validation passed.

## Blockers

None.
