Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-add-dagster-asset-graph.md

# Dagster Asset Graph Evidence

## What Was Observed

Implemented the Dagster GitHub asset graph for the existing bronze and silver flow.

Changed implementation/docs/tests:

- `src/kabuto_kurage/assets/__init__.py`
- `src/kabuto_kurage/assets/github.py`
- `src/kabuto_kurage/definitions.py`
- `tests/test_dagster_assets.py`
- `docs/dagster-asset-graph.md`
- `docs/development.md`
- `README.md`
- `.loom/tickets/2026-06-18-add-dagster-asset-graph.md`

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
uv run python -c "from kabuto_kurage.definitions import defs; print(len(defs.assets or []))"
uv run python - <<'PY'
from kabuto_kurage.definitions import defs
print(sorted(spec.key.to_user_string() for spec in defs.resolve_all_asset_specs()))
PY

# Live CLI materialization used a temporary DAGSTER_HOME, tenant config, data root,
# and GITHUB_TOKEN supplied from `gh auth token` without printing the token.
GITHUB_TOKEN="$(gh auth token)" \
KABUTO_TENANTS_CONFIG="$cfg" \
KABUTO_DATA_ROOT="$tmpdir/data" \
KABUTO_GITHUB_MAX_REPOSITORIES=1 \
DAGSTER_HOME="$tmpdir/dagster" \
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests

git status --short
```

## Validation Output

`uv run pytest`:

```text
collected 25 items

tests/test_dagster_assets.py ..
tests/test_github_bronze_ingestion.py ....
tests/test_github_silver_models.py .....
tests/test_scaffold.py ...
tests/test_tenancy.py ...........

25 passed in 2.48s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 10 source files
```

Dagster definitions sanity:

```text
2
```

The count is 2 because the four asset keys are implemented as two multi-assets: one bronze multi-asset and one silver multi-asset.

Asset key inspection:

```text
['github_bronze_pull_requests', 'github_bronze_repositories', 'github_silver_pull_requests', 'github_silver_repositories']
```

Live Dagster CLI materialization also succeeded against GitHub using a temporary config for `octocat/Hello-World`. The run materialized all four assets and ended with:

```text
ASSET_MATERIALIZATION - Materialized value github_bronze_repositories.
ASSET_MATERIALIZATION - Materialized value github_bronze_pull_requests.
ASSET_MATERIALIZATION - Materialized value github_silver_repositories.
ASSET_MATERIALIZATION - Materialized value github_silver_pull_requests.
RUN_SUCCESS - Finished execution of run for "__ASSET_JOB__".
```

`tests/test_dagster_assets.py` materialized the bronze and silver asset graph with partition `sandbox` using a monkeypatched GitHub ingestion function. No live GitHub token or network access was required for automated tests. The test validated:

- all four asset materializations were emitted;
- each materialization included row count, tenant ID, source, Delta table path, and Delta version metadata;
- bronze materialization included rate-limit metadata;
- silver materialization included latest bronze ingestion lineage metadata;
- silver pull request Delta output was written for the sandbox tenant.

`git status --short` after validation showed expected unstaged/untracked implementation, docs, test, ticket, and evidence changes only.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-add-dagster-asset-graph.md` because:

- The Dagster code location exposes the four required GitHub asset keys.
- The assets are tenant-partitioned and materializable through Dagster.
- The graph reuses existing bronze ingestion and silver transform code instead of duplicating pipeline logic.
- Asset materializations include useful row count, tenant/source, Delta path, Delta version, and lineage/rate-limit metadata.
- README and `docs/dagster-asset-graph.md` document how to open Dagster UI and materialize the graph.
- Tests validate the materialization path without live GitHub dependency.
- Live Dagster CLI materialization against GitHub also succeeded with a temporary data root and token supplied by the local GitHub CLI.

## Limits

This evidence does not prove gold metrics, REST API/MCP/dashboard behavior, schedules/sensors, or live browser-based Dagster UI clicks. Live Dagster materialization still requires an operator-provided `GITHUB_TOKEN` or `GH_TOKEN`, as documented.
