Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-add-taskfile-developer-workflow.md
Depends-On: .loom/tickets/2026-06-19-add-taskfile-developer-workflow.md

# Fix Taskfile Dagster Home Path

## Scope

Fix `task dagster` failing because Dagster rejects relative `DAGSTER_HOME` values.

## Acceptance Criteria

- `task dagster` resolves the default `.local/dagster` path to an absolute path before invoking Dagster.
- `task materialize` uses the same absolute-path convention.
- Docs explain that Dagster requires absolute `DAGSTER_HOME`.
- Taskfile tests cover this behavior.

## Current State

Done. Taskfile now resolves `DAGSTER_HOME` to an absolute path for Dagster UI and materialization commands.

## Journal

- 2026-06-19: User reported `task dagster` failed with `DagsterInvariantViolationError: $DAGSTER_HOME ".local/dagster" must be an absolute path`.
- 2026-06-19: Updated `Taskfile.yml` to convert relative `dagster_home` values to `$PWD/<path>` before invoking Dagster.
- 2026-06-19: Updated README/development/Dagster docs and Taskfile tests.
- 2026-06-19: Validated with `task --dry dagster`, focused pytest, ruff, and mypy.

## Blockers

None.
