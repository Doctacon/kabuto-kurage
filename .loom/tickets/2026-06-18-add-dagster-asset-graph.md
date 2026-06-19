Status: done
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

## Current State

Done. Dagster is now the first user-facing surface for the GitHub-to-Delta flow.

Implemented:

- `src/kabuto_kurage/assets/github.py` with tenant-partitioned Dagster assets:
  - `github_bronze_repositories`
  - `github_bronze_pull_requests`
  - `github_silver_repositories`
  - `github_silver_pull_requests`
- `src/kabuto_kurage/definitions.py` now exposes the GitHub asset graph through `defs`.
- Bronze assets reuse existing `ingest_tenant_github_to_bronze()` logic.
- Silver assets reuse existing `materialize_tenant_github_silver()` logic.
- Assets are statically partitioned by configured tenant IDs from the active tenant registry.
- Asset materializations include tenant/source/layer/resource metadata, row counts, Delta table paths, Delta versions, data root, ingestion run/fetched timestamp where available, rate-limit snapshots for bronze, and latest bronze lineage for silver.
- `docs/dagster-asset-graph.md`, README, and `docs/development.md` document Dagster UI startup, tenant partitions, CLI materialization, and metadata.
- `tests/test_dagster_assets.py` validates the asset keys, tenant partitions, and fixture-backed materialization path without requiring live GitHub.

Evidence: `.loom/evidence/2026-06-18-dagster-asset-graph.md`.

Review: `.loom/reviews/2026-06-18-dagster-asset-graph-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added Dagster GitHub asset definitions and wired `kabuto_kurage.definitions` to the GitHub asset graph.
- 2026-06-18: Added `docs/dagster-asset-graph.md` and updated README/development docs with UI and CLI materialization instructions.
- 2026-06-18: Added tests covering asset definitions, tenant partitions, and materialization with mocked/fixture-backed GitHub ingestion.
- 2026-06-18: Ran `uv run pytest`; 25 tests passed.
- 2026-06-18: Ran `uv run ruff check .`; passed.
- 2026-06-18: Ran `uv run mypy src`; passed.
- 2026-06-18: Ran Dagster definitions sanity checks showing two multi-asset definitions and four asset keys.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- Dagster UI/code location shows the core asset graph through four asset keys under `kabuto_kurage.definitions`.
- The first end-to-end GitHub bronze-to-silver flow is materializable through Dagster UI or the documented `dagster asset materialize` CLI command.
- Asset materializations include useful metadata: row counts, tenant/source/layer/resource values, Delta table paths, Delta versions, data root, ingestion run/fetched timestamp where available, rate-limit snapshots for bronze, and lineage metadata for silver.
- README documents how to open Dagster UI and run/materialize the assets.
- Automated tests validate asset definitions and materialization without live GitHub dependency.

## Blockers

None for this ticket. Live Dagster materialization still requires an operator-provided `GITHUB_TOKEN` or `GH_TOKEN`, as documented.
