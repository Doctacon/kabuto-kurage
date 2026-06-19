Status: open
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

## Progress and Notes

- Not started.

## Blockers

- Requires core Dagster asset graph and metrics.
