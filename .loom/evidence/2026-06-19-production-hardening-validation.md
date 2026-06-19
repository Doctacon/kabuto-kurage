Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-production-harden-github-pipeline.md

# Production Hardening Validation

## Implemented

The GitHub pipeline now includes the four requested production-looking upgrades:

1. Dagster asset checks: one `delta_table_health` check per GitHub asset validates Delta table existence, required columns, minimum row counts, and tenant scope.
2. Incremental PR sync: pull-request ingestion persists `updated_at` cursor state in `.local/data/dlt/github/{tenant_id}/incremental_state.json`, applies a configurable lookback, fetches recently updated PR pages after the first run, and merges changed bronze rows with the existing snapshot by `source_id`.
3. GitHub App auth: ingestion supports `KABUTO_GITHUB_AUTH_MODE=auto|pat|app`; auto uses `GITHUB_TOKEN`/`GH_TOKEN` if present and otherwise mints a short-lived installation token from `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, and `GITHUB_APP_PRIVATE_KEY_PATH`/`GITHUB_APP_PRIVATE_KEY`.
4. Dagster schedules/retries: `github_assets_job` has a two-attempt op retry policy and a stopped-by-default six-hour `github_assets_refresh_schedule` that yields one run per tenant partition when enabled.

## Deterministic Validation

Commands run:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

Observed:

```text
All checks passed!
Success: no issues found in 18 source files
90 passed, 3 warnings
```

New deterministic coverage includes:

- Dagster definitions expose six asset checks, retry policy, and stopped schedule.
- Incremental PR sync preserves existing bronze rows while adding changed PR rows and writing cursor state.
- GitHub App installation-token minting is unit-tested with a mocked session/JWT.

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

GitHub App support is implemented and unit-tested, but live GitHub App validation still requires creating/installing an app and storing its app ID, installation ID, and private key in Proton Pass or another secret store. The schedule is intentionally stopped by default so local development does not unexpectedly poll GitHub.
