Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-add-observability-and-freshness.md

# Observability and Freshness Evidence

## What Was Observed

Implemented lightweight local observability and freshness inspection for the GitHub Delta data platform.

Changed implementation/docs/tests:

- `src/kabuto_kurage/observability.py`
- `tools/observe_github.py`
- `src/kabuto_kurage/assets/github.py`
- `tests/test_observability.py`
- `tests/test_dagster_assets.py`
- `docs/observability.md`
- `docs/dagster-asset-graph.md`
- `docs/development.md`
- `README.md`
- `.loom/tickets/2026-06-18-add-observability-and-freshness.md`

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
tmpdir=$(mktemp -d); uv run python tools/observe_github.py --tenant sandbox --data-root "$tmpdir" --format table
git status --short
```

## Validation Output

`uv run pytest`:

```text
collected 37 items

tests/test_dagster_assets.py ..
tests/test_github_bronze_ingestion.py ....
tests/test_github_gold_metrics.py .....
tests/test_github_silver_models.py .....
tests/test_observability.py ....
tests/test_scaffold.py ...
tests/test_tenancy.py ...........
tests/test_tenant_isolation.py ...

37 passed in 2.77s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 12 source files
```

Local observability command against an empty temporary data root:

```text
tenant   layer   resource             rows  freshness  lag_hours  latest_ingested  run_id  rate_remaining
-------  ------  -------------------  ----  ---------  ---------  ---------------  ------  --------------
sandbox  bronze  repositories         0     missing
sandbox  bronze  pull_requests        0     missing
sandbox  silver  repositories         0     missing
sandbox  silver  pull_requests        0     missing
sandbox  gold    pr_throughput_daily  0     missing
sandbox  gold    pr_cycle_time        0     missing
```

`tests/test_observability.py` also validates fixture-backed non-empty behavior:

- table existence and row count;
- latest successful ingestion timestamp and run ID;
- freshness lag/status;
- bronze GitHub rate-limit fields;
- missing and empty table behavior;
- JSON CLI output.

`tests/test_dagster_assets.py` validates Dagster materialization metadata includes operational fields such as `observed_row_count`, `freshness_status`, `latest_successful_ingestion_at`, and `latest_ingestion_run_id`.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-add-observability-and-freshness.md` because:

- Dagster materializations expose local operational/freshness metadata.
- `tools/observe_github.py` provides a local command for last-ingested state, row counts, freshness/lag, missing/empty tables, and rate-limit status.
- Row count and freshness/lag signals are available by tenant/source/layer/resource for all known GitHub bronze, silver, and gold tables.
- Tests cover failure/empty-data behavior through missing and empty Delta table cases.
- README and docs explain stale/failed ingestion detection without adding external observability infrastructure.

## Limits

This evidence does not prove production observability, alerting, tracing, retries, Prometheus/Grafana, PagerDuty, REST APIs, MCP, or dashboards. Those are intentionally out of scope. Freshness is a local heuristic based on lineage timestamps and a configurable stale threshold, not a production SLA.
