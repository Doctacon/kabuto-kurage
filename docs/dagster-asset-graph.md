# Dagster GitHub Asset Graph

Dagster is the first user-facing surface for `kabuto-kurage`. The code location at `kabuto_kurage.definitions` exposes a partitioned GitHub asset graph that moves one tenant's GitHub data through Delta Lake:

```text
github_bronze_repositories ┐
                           ├─> github_silver_repositories
github_bronze_pull_requests ┘

                           ┌─> github_silver_pull_requests ──> github_gold_pr_throughput_daily
github_bronze_repositories ┤                              └──> github_gold_pr_cycle_time
github_bronze_pull_requests ┘
```

## Assets

| Asset | Layer | Resource | What it does |
| --- | --- | --- | --- |
| `github_bronze_repositories` | bronze | repositories | Ingests raw GitHub repository payloads to tenant-scoped bronze Delta. |
| `github_bronze_pull_requests` | bronze | pull requests | Ingests raw GitHub pull request payloads to tenant-scoped bronze Delta. |
| `github_silver_repositories` | silver | repositories | Builds the typed repository silver model from bronze Delta. |
| `github_silver_pull_requests` | silver | pull requests | Builds the typed pull-request silver model from bronze Delta. |
| `github_gold_pr_throughput_daily` | gold | PR throughput daily | Computes daily opened/merged/closed PR counts by tenant and repository. |
| `github_gold_pr_cycle_time` | gold | PR cycle time | Computes per-PR open-to-merge duration fields. |

The two bronze assets are produced by one Dagster multi-asset because the existing GitHub ingestion function fetches repositories and pull requests in one bounded batch. The two silver assets are also produced together because the existing silver transform materializes both modeled tables from bronze. The two gold assets are produced together because they both derive from the silver pull-request table.

## Asset Checks, Retries, and Schedule

Dagster definitions now include one `delta_table_health` check per asset. Each check validates that the Delta table exists, required columns are present, row counts meet the configured minimum, and every row belongs to the selected tenant partition.

The `github_assets_job` has an op retry policy of two retries with a 30 second delay. A stopped-by-default schedule named `github_assets_refresh_schedule` is included to show the intended production orchestration shape without unexpectedly polling GitHub during local development. If manually enabled, it emits one run per configured tenant every six hours (`0 */6 * * *`).

## Tenant Partitions

Each asset is statically partitioned by configured `tenant_id`. The partition set is loaded from the active tenant registry when the Dagster code location starts:

- `KABUTO_TENANTS_CONFIG` if set.
- Otherwise `config/tenants.example.yaml`.

The committed example partitions are `oss_projects`, `personal`, and `sandbox`. Restart Dagster after changing tenant config so the partition list refreshes.

## Start Dagster UI

```bash
export DAGSTER_HOME="$PWD/.local/dagster"
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

Or use the Taskfile wrapper, which resolves the default Dagster home to an absolute path for you:

```bash
task dagster
```

Open the URL printed by Dagster, select a tenant partition such as `personal`, `oss_projects`, or `sandbox`, and materialize the GitHub assets. Set `GITHUB_TOKEN` or `GH_TOKEN` before materializing bronze assets against the live GitHub API. If neither token nor fixture mode is configured, `task dagster` prints a warning before launching the UI because bronze materialization will fail without one of those inputs.

For deterministic no-token demos and smoke tests, start Dagster with fixture mode:

```bash
KABUTO_GITHUB_FIXTURE_MODE=1 task dagster
```

Fixture mode writes one synthetic repository and pull request through the same bronze, silver, and gold assets. It is intended for local demos/tests, not live ingestion.

For safer local demos, limit discovered repositories before starting Dagster:

```bash
export KABUTO_GITHUB_MAX_REPOSITORIES=1
```

## CLI Materialization

The same graph can be materialized without opening the UI:

```bash
export GITHUB_TOKEN=...
export KABUTO_GITHUB_MAX_REPOSITORIES=1
export DAGSTER_HOME="$PWD/.local/dagster"
mkdir -p "$DAGSTER_HOME"
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests,github_gold_pr_throughput_daily,github_gold_pr_cycle_time
```

This writes tenant-scoped Delta tables under:

```text
.local/data/delta/tenants/{tenant_id}/bronze/github/repositories
.local/data/delta/tenants/{tenant_id}/bronze/github/pull_requests
.local/data/delta/tenants/{tenant_id}/silver/github/repositories
.local/data/delta/tenants/{tenant_id}/silver/github/pull_requests
.local/data/delta/tenants/{tenant_id}/gold/github/pr_throughput_daily
.local/data/delta/tenants/{tenant_id}/gold/github/pr_cycle_time
```

## Asset Metadata

Each materialization includes metadata intended to make the Dagster UI useful for learning and debugging:

- `tenant_id`
- `source`
- `layer`
- `resource_type`
- `row_count`
- `delta_table_path`
- `delta_version`
- `data_root`
- `observed_row_count`
- `freshness_status`
- `freshness_lag_seconds` / `freshness_lag_hours` when lineage timestamps are present
- `latest_successful_ingestion_at` and `latest_ingestion_run_id` when lineage columns are present
- Bronze-only: `ingestion_run_id`, `fetched_at`, `rate_limit_snapshots`, `minimum_rate_limit_remaining`, and observed `rate_limit_*` fields when GitHub returns rate-limit headers.
- Silver-only: latest bronze `ingestion_run_id` and `fetched_at` observed in the silver table when available.
- Gold-only: metric grain/unit notes such as `tenant_repository_day` for throughput and `hours_and_days` for cycle time.

Use `uv run python tools/observe_github.py --tenant sandbox --format table` outside Dagster to inspect the same freshness and row-count signals across all known GitHub tables.

## Out of Scope

This milestone still does not add dashboards, sensors, review/comment ingestion, production deployment, or alert delivery. REST, MCP, stopped-by-default schedules, retries, and asset checks are implemented in the current local project.
