Status: done
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

## Current State

Done. Tenant-scoped GitHub gold metrics are computed from the silver pull request model and stored as gold Delta tables.

Implemented:

- `src/kabuto_kurage/transforms/github_gold.py` with:
  - `pr_throughput_daily`: daily opened/merged/closed PR counts by tenant and repository;
  - `pr_cycle_time`: per-PR open-to-merge duration fields in hours and days;
  - tenant materialization into gold Delta tables;
  - CLI argument parsing.
- `tools/build_github_gold.py` CLI wrapper.
- `src/kabuto_kurage/assets/github.py` updated with Dagster gold assets:
  - `github_gold_pr_throughput_daily`;
  - `github_gold_pr_cycle_time`.
- `tests/test_github_gold_metrics.py` covering deterministic metric calculations, gold Delta writes, schema presence, and tenant path separation.
- `tests/test_dagster_assets.py` updated to validate gold assets and downstream materialization.
- `docs/github-gold-metrics.md` documenting metric grain, columns, interpretation, and limitations.
- README, `docs/development.md`, and `docs/dagster-asset-graph.md` updated with gold metric commands and Dagster asset details.

Evidence: `.loom/evidence/2026-06-18-gold-engineering-metrics.md`.

Review: `.loom/reviews/2026-06-18-gold-engineering-metrics-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added GitHub gold transform module, CLI wrapper, gold Dagster assets, deterministic tests, and metric documentation.
- 2026-06-18: Ran `uv run pytest`; 30 tests passed.
- 2026-06-18: Ran `uv run ruff check .`; passed.
- 2026-06-18: Ran `uv run mypy src`; passed.
- 2026-06-18: Ran Dagster definitions inspection; six GitHub assets are exposed including the two gold metric assets.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- At least two useful tenant-scoped metrics are computed:
  - `pr_throughput_daily` for daily opened/merged/closed PR counts;
  - `pr_cycle_time` for per-PR open-to-merge duration.
- Metrics are written to gold Delta tables under tenant-scoped paths:
  - `.local/data/delta/tenants/{tenant_id}/gold/github/pr_throughput_daily`;
  - `.local/data/delta/tenants/{tenant_id}/gold/github/pr_cycle_time`.
- Dagster exposes `github_gold_pr_throughput_daily` and `github_gold_pr_cycle_time` assets downstream of `github_silver_pull_requests`.
- Deterministic tests validate metric calculations, Delta materialization, tenant path separation, and Dagster materialization.
- Documentation explains metric meaning, columns, interpretation, and limitations.

## Blockers

None for this ticket. Review latency and richer production-grade metric semantics require additional source resources and future product decisions.
