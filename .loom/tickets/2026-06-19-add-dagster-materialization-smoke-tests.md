Status: active
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-add-dagster-asset-graph.md
Depends-On: .loom/tickets/2026-06-18-add-dagster-asset-graph.md, .loom/tickets/2026-06-19-add-taskfile-developer-workflow.md

# Add Dagster Materialization Smoke Tests

## Scope

The user observed that `task dagster` starts the UI but asset materialization fails when no `GITHUB_TOKEN`/`GH_TOKEN` is exported. Strengthen the test and developer workflow so the project has an actual Dagster materialization smoke path that does not require live GitHub credentials, and so the UI workflow gives clear preflight guidance before users click materialize.

## Acceptance Criteria

- There is a deterministic Dagster CLI materialization smoke test for the full bronze→silver→gold asset chain without live GitHub credentials.
- The smoke path does not require printing or committing secrets.
- `task dagster` warns clearly when neither GitHub token nor fixture mode is configured.
- Docs explain how to run Dagster with a live token and how to run a fixture/demo mode.
- Full validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Current State

Done. The project now has a deterministic Dagster CLI materialization smoke test for the full asset chain and a clearer UI launch warning when live credentials or fixture mode are missing.

## Journal

- 2026-06-19: Created after user reported Dagster UI materialization failure due to missing GitHub token and requested better testing.
- 2026-06-19: Added `KABUTO_GITHUB_FIXTURE_MODE=1` as an explicit deterministic no-token demo/smoke path for bronze ingestion.
- 2026-06-19: Added `tests/test_dagster_cli_materialization.py`, which invokes the real Dagster CLI and asserts the full bronze→silver→gold asset chain reaches `RUN_SUCCESS` without live GitHub credentials.
- 2026-06-19: Updated `task dagster` to warn if no GitHub token and no fixture mode are configured.
- 2026-06-19: Updated docs and tests for fixture mode and preflight guidance.
- 2026-06-19: Recorded evidence in `.loom/evidence/2026-06-19-dagster-materialization-smoke-validation.md`.

## Results

Acceptance criteria satisfied:

- Deterministic Dagster CLI materialization smoke test exists and covers the full bronze→silver→gold asset chain.
- The smoke path uses fixture mode and does not require printing or committing secrets.
- `task dagster` warns clearly when neither GitHub token nor fixture mode is configured.
- Docs explain live-token and fixture-mode Dagster paths.
- Full validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Blockers

None.
