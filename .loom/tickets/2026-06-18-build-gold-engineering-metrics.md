Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-build-silver-github-models.md, .loom/tickets/2026-06-18-add-dagster-asset-graph.md

# Build Gold Engineering Metrics

## Scope

Compute the first tenant-scoped product metrics from silver GitHub models.

Initial metric candidates:

- Pull request throughput by tenant/repository/time window.
- Pull request open-to-merge cycle time.
- Review latency if review data is available or added.
- Open vs merged PR counts.

Expected behavior:

- Metrics are stored as gold Delta tables or equivalent selected metric layer.
- Metrics are visible through Dagster asset materializations and metadata.
- Queries/examples demonstrate tenant-scoped reads.

## Out of Scope

- Complete Jellyfish metric parity.
- Proprietary allocation models.
- Customer-facing REST API unless separately scheduled.

## Acceptance Criteria

- At least two useful tenant-scoped metrics are computed.
- Metrics have tests using deterministic fixtures.
- Dagster UI shows metric assets downstream of silver models.
- Documentation explains what each metric means and its limitations.

## Progress and Notes

- Not started.

## Blockers

- Requires silver models and Dagster assets.
