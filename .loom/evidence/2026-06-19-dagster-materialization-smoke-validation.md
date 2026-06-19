Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-add-dagster-materialization-smoke-tests.md

# Dagster Materialization Smoke Validation

## What Was Observed

A deterministic no-token Dagster CLI materialization smoke test was added after the UI workflow showed bronze asset failures when no `GITHUB_TOKEN` or `GH_TOKEN` was exported.

Validation commands run:

```bash
uv run pytest tests/test_dagster_cli_materialization.py tests/test_taskfile_workflow.py -q
uv run pytest
uv run ruff check .
uv run mypy src
```

Observed output summary:

```text
8 passed in 13.68s
87 passed, 2 warnings in 17.95s
All checks passed!
Success: no issues found in 18 source files
```

The new smoke test invokes the real Dagster CLI:

```bash
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests,github_gold_pr_throughput_daily,github_gold_pr_cycle_time
```

with a temporary tenant config, temporary `DAGSTER_HOME`, temporary `KABUTO_DATA_ROOT`, and `KABUTO_GITHUB_FIXTURE_MODE=1`. It asserts `RUN_SUCCESS`, verifies all six Delta tables exist, and verifies dlt schema/state artifacts are written.

## Procedure

Fixture mode was added as an explicit deterministic local demo/smoke path. When `KABUTO_GITHUB_FIXTURE_MODE=1` is set, bronze ingestion emits one synthetic repository and pull request through the same dlt source/resource, bronze, silver, and gold asset chain without requiring live GitHub credentials.

`task dagster` now warns if neither `GITHUB_TOKEN`/`GH_TOKEN` nor fixture mode is configured, so users know before launching the UI that bronze materialization will fail unless they export a token or intentionally choose fixture mode.

## What This Supports or Challenges

Supports that the project now has a real Dagster CLI materialization test for the full asset chain and clearer developer feedback for missing live credentials.

## Limits

This evidence does not prove live GitHub connectivity. Live materialization still requires `GITHUB_TOKEN` or `GH_TOKEN`. Fixture mode is for deterministic local demo/testing only and should not be presented as live ingestion evidence.
