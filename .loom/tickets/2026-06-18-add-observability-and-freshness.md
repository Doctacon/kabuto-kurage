Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-add-dagster-asset-graph.md, .loom/tickets/2026-06-18-build-gold-engineering-metrics.md

# Add Observability and Freshness

## Scope

Add enough observability for the portfolio project to tell an operational story.

Expected signals:

- Last successful ingestion by tenant/source/resource.
- Row counts by layer and tenant.
- GitHub API rate-limit status where available.
- Freshness or lag indicator.
- Failure/retry behavior documented or represented.
- Dagster asset metadata for operational state.

## Out of Scope

- Full Prometheus/Grafana stack unless later chosen.
- PagerDuty/Slack integrations.
- Production SLOs.

## Acceptance Criteria

- Dagster materializations expose freshness/run metadata.
- A local command or documented query shows last-ingested state by tenant/source.
- README or docs explain how to detect stale or failed ingestion.
- At least one test or fixture covers failure/empty-data behavior.

## Current State

Done. The local platform now has lightweight observability and freshness signals without adding an external observability stack.

Implemented:

- `src/kabuto_kurage/observability.py` collects table existence, row counts, Delta versions, latest successful ingestion timestamps, latest run IDs, freshness lag/status, and GitHub rate-limit summaries for known tenant-scoped GitHub bronze/silver/gold Delta tables.
- `tools/observe_github.py` exposes local JSON or compact table output by tenant or all configured tenants.
- Dagster asset materializations now include local operational metadata where relevant: `observed_row_count`, `freshness_status`, `freshness_lag_seconds`, `freshness_lag_hours`, `latest_successful_ingestion_at`, `latest_ingestion_run_id`, and bronze rate-limit fields.
- `docs/observability.md`, README, `docs/development.md`, and `docs/dagster-asset-graph.md` explain how to inspect freshness, row counts, last-ingested state, missing/empty tables, rate-limit status, and likely failed/stale ingestion.
- `tests/test_observability.py` covers missing tables, empty tables, fresh/stale status, row counts, rate-limit extraction, and CLI JSON output without live GitHub.
- `tests/test_dagster_assets.py` validates operational metadata on Dagster materializations.

Evidence: `.loom/evidence/2026-06-18-observability-and-freshness.md`.

Review: `.loom/reviews/2026-06-18-observability-and-freshness-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added local observability collector and CLI command.
- 2026-06-18: Added Dagster freshness/run metadata sourced from Delta table observations.
- 2026-06-18: Added tests for missing/empty/fresh/stale/rate-limit/CLI behavior and updated Dagster asset metadata tests.
- 2026-06-18: Added observability docs and README/development/Dagster metadata guidance.
- 2026-06-18: Ran `uv run pytest`, `uv run ruff check .`, `uv run mypy src`, and a local `tools/observe_github.py` command against an empty temporary data root successfully.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- Dagster materializations expose freshness/run metadata where relevant.
- `uv run python tools/observe_github.py --tenant sandbox --format table` shows last-ingested state, row counts, freshness status/lag, and rate-limit status where present.
- Freshness/lag and row count signals are available by tenant/source/layer/resource for all known GitHub bronze, silver, and gold tables.
- Tests cover failure/empty-data behavior through missing and empty Delta tables.
- README and docs explain how to detect stale or failed ingestion locally.

## Blockers

None for this ticket. Production observability, retries, alerts, dashboards, REST APIs, and MCP remain out of scope.
