# GitHub Gold Engineering Metrics

This milestone adds the first tenant-scoped gold metric tables derived from the silver GitHub pull request model.

The goal is not to recreate Jellyfish metrics. These are intentionally simple, auditable portfolio metrics that demonstrate how raw GitHub activity can become product-facing engineering intelligence.

## Running Locally

Run bronze ingestion and silver modeling first:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox --max-repositories 1
uv run python tools/build_github_silver.py --tenant sandbox
```

Then build gold metrics:

```bash
uv run python tools/build_github_gold.py --tenant sandbox
```

Or build all configured tenants:

```bash
uv run python tools/build_github_gold.py --all-tenants
```

For temporary validation data roots, pass the same `--data-root` to all three commands.

## Storage Layout

Gold tables follow the same tenant-scoped Delta path convention as bronze and silver:

```text
.local/data/delta/tenants/{tenant_id}/gold/github/pr_throughput_daily
.local/data/delta/tenants/{tenant_id}/gold/github/pr_cycle_time
```

Writes use overwrite semantics for this local snapshot-style metric layer. Re-running gold metrics replaces the tenant's current metric snapshot with values derived from the latest silver pull request table.

## Metric: `gold/github/pr_throughput_daily`

Purpose: show daily pull request activity by tenant and repository.

Grain:

```text
one row per tenant_id + repository_full_name + metric_date
```

Columns:

| Column | Type | Meaning |
| --- | --- | --- |
| `tenant_id` | string | Logical tenant ID. |
| `source` | string | Source system, currently `github`. |
| `repository_full_name` | string | GitHub `owner/name`. |
| `metric_date` | date | Date of the observed PR event. |
| `opened_count` | int64 | Count of PRs whose `created_at` date is `metric_date`. |
| `merged_count` | int64 | Count of PRs whose `merged_at` date is `metric_date`. |
| `closed_count` | int64 | Count of PRs whose `closed_at` date is `metric_date`. |
| `observed_pull_request_count` | int64 | Distinct PRs contributing any event to this row. |
| `latest_fetched_at` | timestamp UTC | Latest silver `fetched_at` among contributing PRs. |
| `latest_ingestion_run_id` | string | Ingestion run associated with the latest contributing fetch timestamp. |

Interpretation:

- `opened_count` approximates intake/new PR activity.
- `merged_count` approximates completed PR throughput.
- `closed_count` includes merged and unmerged closures because GitHub PRs can close without merging.

Limitations:

- Counts are based only on repositories included in the tenant config and current silver snapshot.
- Dates are UTC dates derived from GitHub timestamps.
- This table does not distinguish human-authored PRs from bots or AI agents yet.
- This table does not deduplicate across forks beyond the current silver `repository_full_name` logic.

## Metric: `gold/github/pr_cycle_time`

Purpose: show per-pull-request open-to-merge duration for later aggregation and exploration.

Grain:

```text
one row per observed pull request in the tenant's silver table
```

Columns:

| Column | Type | Meaning |
| --- | --- | --- |
| `tenant_id` | string | Logical tenant ID. |
| `source` | string | Source system, currently `github`. |
| `repository_full_name` | string | Base repository `owner/name`. |
| `repository_owner` | string | Owner parsed from `repository_full_name`. |
| `pull_request_id` | int64 | GitHub pull request numeric ID. |
| `pull_request_node_id` | string | GitHub GraphQL/global node ID. |
| `number` | int64 | PR number within the repository. |
| `title` | string | Pull request title. |
| `user_login` | string | PR author login when present. |
| `state` | string | GitHub PR state. |
| `merged` | boolean | Whether the PR has a `merged_at` timestamp. |
| `created_at` | timestamp UTC | PR creation time. |
| `merged_at` | timestamp UTC | PR merge time. |
| `cycle_time_hours` | float64 | Hours between `created_at` and `merged_at`, null when unavailable or invalid. |
| `cycle_time_days` | float64 | `cycle_time_hours / 24`, null when unavailable or invalid. |
| `fetched_at` | timestamp UTC | Silver/bronze ingestion fetch timestamp. |
| `ingestion_run_id` | string | Source ingestion run ID. |

Interpretation:

- For merged PRs with valid timestamps, `cycle_time_hours` is a simple open-to-merge duration.
- Unmerged/open PRs remain in the table with null cycle-time fields so downstream users can choose whether to filter them.

Limitations:

- This is not a full delivery lead-time metric; it starts at PR creation, not issue creation or first commit.
- Review latency is not computed yet because review/comment resources are not ingested in this milestone.
- Draft time, bot PRs, weekends, team ownership, and size/complexity normalization are not modeled yet.
- Negative or malformed durations produce nulls rather than failing the metric build.

## Dagster Assets

The gold tables are exposed as Dagster assets downstream of `github_silver_pull_requests`:

- `github_gold_pr_throughput_daily`
- `github_gold_pr_cycle_time`

Each materialization includes metadata such as `tenant_id`, `source`, `layer`, `resource_type`, `row_count`, `delta_table_path`, `delta_version`, and metric-specific grain/unit notes.

## Out of Scope

This metric milestone does not add REST APIs, MCP, dashboards, proprietary allocation models, review/comment ingestion, or complete Jellyfish metric parity.
