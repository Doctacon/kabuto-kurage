# Local Observability and Freshness

`kabuto-kurage` does not run a production observability stack. Instead, it exposes lightweight local signals from the Delta tables and Dagster materializations that already exist.

The goal is to answer operational questions during local development:

- Did this tenant's GitHub ingestion succeed?
- How many rows exist by tenant, layer, and resource?
- When was the data last fetched from GitHub?
- Is the local snapshot fresh or stale by a simple threshold?
- What GitHub rate-limit status was captured during bronze ingestion?
- Which tables are missing or empty?

## Local Command

Inspect one tenant as JSON:

```bash
uv run python tools/observe_github.py --tenant sandbox
```

Inspect one tenant as a compact table:

```bash
uv run python tools/observe_github.py --tenant sandbox --format table
```

Inspect all configured tenants:

```bash
uv run python tools/observe_github.py --all-tenants --format table
```

Use a temporary data root when validating isolated runs:

```bash
uv run python tools/observe_github.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation \
  --format table
```

Adjust the stale threshold:

```bash
uv run python tools/observe_github.py \
  --tenant sandbox \
  --stale-after-hours 48
```

## Signals

The command emits one record for each known GitHub table:

- `bronze/github/repositories`
- `bronze/github/pull_requests`
- `silver/github/repositories`
- `silver/github/pull_requests`
- `gold/github/pr_throughput_daily`
- `gold/github/pr_cycle_time`

Each record includes:

| Field | Meaning |
| --- | --- |
| `tenant_id` | Tenant partition being inspected. |
| `source` | Source system, currently `github`. |
| `layer` | Lakehouse layer: `bronze`, `silver`, or `gold`. |
| `resource_type` | Resource/table name. |
| `table_exists` | Whether the Delta table path exists. |
| `row_count` | Number of rows in the current Delta table snapshot. |
| `delta_version` | Delta table version, when the table exists. |
| `latest_successful_ingestion_at` | Latest source fetch timestamp observed in the table lineage columns. |
| `latest_ingestion_run_id` | Run ID associated with the latest observed source fetch when available. |
| `freshness_lag_seconds` / `freshness_lag_hours` | Time between now and `latest_successful_ingestion_at`. |
| `freshness_status` | `fresh`, `stale`, `missing`, `empty`, or `unknown`. |
| `rate_limit_*` | GitHub rate-limit fields captured from bronze `rate_limit_json` rows when available. |

## Freshness Status

Freshness is deliberately simple:

- `missing`: the Delta table path does not exist.
- `empty`: the Delta table exists but has zero rows.
- `unknown`: rows exist but no usable lineage timestamp was found.
- `fresh`: latest observed source fetch is within `--stale-after-hours`.
- `stale`: latest observed source fetch is older than `--stale-after-hours`.

The default stale threshold is 24 hours. This is a local development heuristic, not a production SLA.

## Dagster Metadata

Dagster asset materializations include the same operational fields where relevant:

- `observed_row_count`
- `freshness_status`
- `freshness_lag_seconds`
- `freshness_lag_hours`
- `latest_successful_ingestion_at`
- `latest_ingestion_run_id`
- bronze rate-limit fields such as `rate_limit_remaining_min`

Existing asset metadata still includes `row_count`, `tenant_id`, `source`, `layer`, `resource_type`, `delta_table_path`, and `delta_version`.

In Dagster UI, stale data usually means the bronze ingestion asset should be materialized again for the tenant partition, then downstream silver and gold assets should be rematerialized.

## Detecting Failed Ingestion

A failed bronze ingestion run raises an error and does not overwrite existing bronze tables because API fetches complete before Delta writes begin. To detect likely failures locally:

1. Check Dagster run status for failed materializations.
2. Run `uv run python tools/observe_github.py --tenant <tenant> --format table`.
3. Look for:
   - `missing` bronze tables: ingestion has never successfully written the resource.
   - `empty` bronze tables: ingestion succeeded but produced no rows for the configured scope.
   - `stale` bronze tables: last successful fetch is older than the threshold.
   - low `rate_remaining`: GitHub API quota may be close to exhaustion.

## Limits

This is not a production observability system. It does not provide Prometheus metrics, Grafana dashboards, alerting, tracing, retries, PagerDuty, or Slack notifications. Those are intentionally out of scope for this local milestone.
