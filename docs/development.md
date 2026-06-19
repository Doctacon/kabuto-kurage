# Development

This document mirrors the command surface in the README for quick reference.

## Environment

```bash
uv sync
cp .env.example .env
```

Do not commit `.env` or generated data under `.local/`.

## Checks

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

## GitHub bronze ingestion

```bash
export GITHUB_TOKEN=...
uv run python tools/ingest_github_bronze.py --tenant sandbox
```

For a bounded validation run that does not write to the default local data root:

```bash
uv run python tools/ingest_github_bronze.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation \
  --max-repositories 1
```

## GitHub silver models

After bronze ingestion has produced tenant-scoped Delta tables:

```bash
uv run python tools/build_github_silver.py --tenant sandbox
```

For temporary validation data roots, use the same `--data-root` used for bronze ingestion.

## Dagster

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

The Dagster code location exposes four tenant-partitioned GitHub assets:

- `github_bronze_repositories`
- `github_bronze_pull_requests`
- `github_silver_repositories`
- `github_silver_pull_requests`

Set `GITHUB_TOKEN` or `GH_TOKEN`, choose a tenant partition such as `sandbox`, and materialize the graph from the UI. For safe demos, set `KABUTO_GITHUB_MAX_REPOSITORIES=1` before starting Dagster.

CLI equivalent:

```bash
export GITHUB_TOKEN=...
export KABUTO_GITHUB_MAX_REPOSITORIES=1
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests
```

See `docs/dagster-asset-graph.md` for asset metadata and graph details.
