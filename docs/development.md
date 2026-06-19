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

## Local IaC

Terraform prepares ignored local runtime files for Dagster and Delta data roots:

```bash
terraform -chdir=iac/local init
terraform -chdir=iac/local apply
```

Use the generated environment file in a shell:

```bash
set -a
source .local/runtime/kabuto.env
set +a
```

Optional Docker Compose Dagster service:

```bash
docker-compose --env-file .local/runtime/kabuto.env -f iac/local/docker-compose.yml up dagster
```

Terraform manages generated local config/files only. Docker Compose runs the optional local process. Neither path provisions cloud/Kubernetes resources or secrets. Use `docker compose` with the same arguments if your environment has the Compose plugin instead of `docker-compose`. See `docs/local-iac.md`.

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

## GitHub gold metrics

After silver models exist:

```bash
uv run python tools/build_github_gold.py --tenant sandbox
```

For temporary validation data roots, use the same `--data-root` used for bronze and silver.

## Local observability

After bronze/silver/gold tables exist, inspect local freshness, row counts, last-ingested state, and rate-limit status:

```bash
uv run python tools/observe_github.py --tenant sandbox --format table
```

Use the same `--data-root` as ingestion/transformation commands when inspecting temporary validation data.

## Dagster

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

The Dagster code location exposes six tenant-partitioned GitHub assets:

- `github_bronze_repositories`
- `github_bronze_pull_requests`
- `github_silver_repositories`
- `github_silver_pull_requests`
- `github_gold_pr_throughput_daily`
- `github_gold_pr_cycle_time`

Set `GITHUB_TOKEN` or `GH_TOKEN`, choose a tenant partition such as `sandbox`, and materialize the graph from the UI. For safe demos, set `KABUTO_GITHUB_MAX_REPOSITORIES=1` before starting Dagster.

CLI equivalent:

```bash
export GITHUB_TOKEN=...
export KABUTO_GITHUB_MAX_REPOSITORIES=1
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests,github_gold_pr_throughput_daily,github_gold_pr_cycle_time
```

Dagster materializations include local operational metadata such as `observed_row_count`, `freshness_status`, `freshness_lag_hours`, `latest_successful_ingestion_at`, `latest_ingestion_run_id`, and bronze rate-limit fields.

See `docs/dagster-asset-graph.md` for asset metadata and graph details. See `docs/observability.md` for the local freshness command and stale/failed ingestion interpretation.
