Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-build-gold-engineering-metrics.md

# Gold Engineering Metrics Evidence

## What Was Observed

Implemented tenant-scoped GitHub gold metrics from silver pull request models.

Changed implementation/docs/tests:

- `src/kabuto_kurage/transforms/github_gold.py`
- `tools/build_github_gold.py`
- `src/kabuto_kurage/assets/github.py`
- `tests/test_github_gold_metrics.py`
- `tests/test_dagster_assets.py`
- `docs/github-gold-metrics.md`
- `docs/dagster-asset-graph.md`
- `docs/development.md`
- `README.md`
- `.loom/tickets/2026-06-18-build-gold-engineering-metrics.md`

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv run python -c "from kabuto_kurage.definitions import defs; print(sorted(s.key.to_user_string() for s in defs.resolve_all_asset_specs()))"
git status --short
```

## Validation Output

`uv run pytest`:

```text
collected 30 items

tests/test_dagster_assets.py ..
tests/test_github_bronze_ingestion.py ....
tests/test_github_gold_metrics.py .....
tests/test_github_silver_models.py .....
tests/test_scaffold.py ...
tests/test_tenancy.py ...........

30 passed in 2.67s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 11 source files
```

Dagster definition inspection:

```text
['github_bronze_pull_requests', 'github_bronze_repositories', 'github_gold_pr_cycle_time', 'github_gold_pr_throughput_daily', 'github_silver_pull_requests', 'github_silver_repositories']
```

`git status --short` after validation showed expected unstaged/untracked implementation, docs, test, ticket, evidence, and review changes only.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-build-gold-engineering-metrics.md` because:

- At least two tenant-scoped metrics are computed from silver GitHub pull requests: daily PR throughput and per-PR open-to-merge cycle time.
- Metrics are written to tenant-scoped gold Delta tables under `.local/data/delta/tenants/{tenant_id}/gold/github/...`.
- Dagster definitions now expose gold assets downstream of `github_silver_pull_requests`.
- Deterministic tests validate pure metric computation, Delta writes, tenant path separation, and Dagster materialization through gold assets.
- Documentation explains metric meanings, columns, interpretation, and limitations.

## Limits

This evidence does not prove review latency, REST API/MCP/dashboard behavior, live GitHub materialization through the Dagster UI, or production-grade metric semantics. Review/comment ingestion and richer metric definitions remain future work.
