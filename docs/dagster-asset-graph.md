# Dagster GitHub Asset Graph

Dagster is the first user-facing surface for `kabuto-kurage`. The code location at `kabuto_kurage.definitions` exposes a partitioned GitHub asset graph that moves one tenant's GitHub data through Delta Lake:

```text
github_bronze_repositories ┐
                           ├─> github_silver_repositories
github_bronze_pull_requests ┘

                           ┌─> github_silver_pull_requests
github_bronze_repositories ┤
github_bronze_pull_requests ┘
```

## Assets

| Asset | Layer | Resource | What it does |
| --- | --- | --- | --- |
| `github_bronze_repositories` | bronze | repositories | Ingests raw GitHub repository payloads to tenant-scoped bronze Delta. |
| `github_bronze_pull_requests` | bronze | pull requests | Ingests raw GitHub pull request payloads to tenant-scoped bronze Delta. |
| `github_silver_repositories` | silver | repositories | Builds the typed repository silver model from bronze Delta. |
| `github_silver_pull_requests` | silver | pull requests | Builds the typed pull-request silver model from bronze Delta. |

The two bronze assets are produced by one Dagster multi-asset because the existing GitHub ingestion function fetches repositories and pull requests in one bounded batch. The two silver assets are also produced together because the existing silver transform materializes both modeled tables from bronze.

## Tenant Partitions

Each asset is statically partitioned by configured `tenant_id`. The partition set is loaded from the active tenant registry when the Dagster code location starts:

- `KABUTO_TENANTS_CONFIG` if set.
- Otherwise `config/tenants.example.yaml`.

Restart Dagster after changing tenant config so the partition list refreshes.

## Start Dagster UI

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

Open the URL printed by Dagster, select a tenant partition such as `sandbox`, and materialize the GitHub assets. Set `GITHUB_TOKEN` or `GH_TOKEN` before materializing bronze assets against the live GitHub API.

For safer local demos, limit discovered repositories before starting Dagster:

```bash
export KABUTO_GITHUB_MAX_REPOSITORIES=1
```

## CLI Materialization

The same graph can be materialized without opening the UI:

```bash
export GITHUB_TOKEN=...
export KABUTO_GITHUB_MAX_REPOSITORIES=1
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests
```

This writes tenant-scoped Delta tables under:

```text
.local/data/delta/tenants/{tenant_id}/bronze/github/repositories
.local/data/delta/tenants/{tenant_id}/bronze/github/pull_requests
.local/data/delta/tenants/{tenant_id}/silver/github/repositories
.local/data/delta/tenants/{tenant_id}/silver/github/pull_requests
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
- Bronze-only: `ingestion_run_id`, `fetched_at`, `rate_limit_snapshots`, and `minimum_rate_limit_remaining` when GitHub returns rate-limit headers.
- Silver-only: latest bronze `ingestion_run_id` and `fetched_at` observed in the silver table when available.

## Out of Scope

This milestone does not add gold metrics, REST APIs, MCP, dashboards, sensors, schedules, or production deployment. Those are tracked by later Loom tickets.
