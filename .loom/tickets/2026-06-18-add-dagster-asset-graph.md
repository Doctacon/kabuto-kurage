Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md, .loom/tickets/2026-06-18-build-silver-github-models.md

# Add Dagster Asset Graph

## Scope

Make Dagster UI the first user-facing surface by representing the GitHub-to-Delta flow as Dagster assets.

Expected assets:

- Bronze GitHub repositories.
- Bronze GitHub pull requests.
- Silver repositories.
- Silver pull requests.

Expected Dagster behavior:

- Local Dagster can start with documented command.
- Assets are materializable from the UI or CLI.
- Asset metadata includes row counts, tenant/source information, and Delta table paths where useful.
- Partitions are considered for tenant/date/source; implement the simplest useful partitioning that does not overcomplicate the first demo.

## Out of Scope

- Full production Dagster deployment.
- Sensor/event queue path unless naturally small.
- Complex backfill automation.

## Acceptance Criteria

- Dagster UI shows the core asset graph.
- A reviewer can materialize the first end-to-end flow from Dagster.
- Asset materializations include useful metadata.
- README documents how to open Dagster UI and run the assets.

## Progress and Notes

- Not started.

## Blockers

- Requires initial ingestion and silver modeling code.
