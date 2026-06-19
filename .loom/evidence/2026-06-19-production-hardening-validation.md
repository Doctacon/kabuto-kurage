Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-production-harden-github-pipeline.md

# Production Hardening Validation

## Implemented

The GitHub pipeline now includes the production-looking upgrades the user wants to keep:

1. Dagster asset checks: one `delta_table_health` check per GitHub asset validates Delta table existence, required columns, minimum row counts, and tenant scope.
2. Incremental PR sync: pull-request ingestion persists `updated_at` cursor state in `.local/data/dlt/github/{tenant_id}/incremental_state.json`, applies a configurable lookback, fetches recently updated PR pages after the first run, and merges changed bronze rows with the existing snapshot by `source_id`.
3. PAT auth: ingestion uses read-only fine-grained PATs through `GITHUB_TOKEN` or `GH_TOKEN`; token values stay outside git and are retrieved locally from Proton Pass when needed.
4. Dagster schedules/retries: `github_assets_job` has a two-attempt op retry policy and a stopped-by-default six-hour `github_assets_refresh_schedule` that yields one run per tenant partition when enabled.

GitHub App auth was removed after the user clarified they do not want to create a GitHub App.

## Deterministic Validation

Commands run:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

Observed after removing GitHub App auth:

```text
All checks passed!
Success: no issues found in 18 source files
89 passed, 3 warnings
```

Coverage includes:

- Dagster definitions expose six asset checks, retry policy, and stopped schedule.
- Incremental PR sync preserves existing bronze rows while adding changed PR rows and writing cursor state.
- PAT/token auth remains fail-closed when `GITHUB_TOKEN`/`GH_TOKEN` is absent outside fixture mode.

## Live Validation

Used Proton Pass item `GitHub API Token`, field `API Key`, as local `GITHUB_TOKEN` without printing the token.

Command:

```bash
task materialize TENANT=personal
```

Observed:

```text
personal hardened materialization RUN_SUCCESS
bronze/repositories: rows=2 freshness=fresh
bronze/pull_requests: rows=33 freshness=fresh
silver/repositories: rows=2 freshness=fresh
silver/pull_requests: rows=33 freshness=fresh
gold/pr_throughput_daily: rows=5 freshness=fresh
gold/pr_cycle_time: rows=33 freshness=fresh
incremental_state_exists=True
incremental_repositories=Doctacon/databox
```

## Limits

The schedule is intentionally stopped by default so local development does not unexpectedly poll GitHub. This remains a local portfolio implementation, not production deployment with cloud secrets, alert delivery, or hosted orchestration.
