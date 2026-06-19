# Development

This document is the quick reference for the local developer workflow. For the portfolio architecture narrative and data-flow diagram, start with `docs/architecture.md`.

## Primary command runner

Taskfile is the primary human-facing command surface for the project. `Taskfile.yml` defines the tasks. The Python scripts in `tools/` remain available as implementation entrypoints, but day-to-day commands should start with `task`.

Install Task from <https://taskfile.dev/> if it is not already available. The project does not install Task automatically.

```bash
task --list
```

Secrets such as `GITHUB_TOKEN`, `GH_TOKEN`, API export tokens, and R2 credentials are read from environment variables by the underlying tools. Task commands intentionally do not echo or interpolate secret values. Store secret values in Proton Pass or another password manager, export them into your shell when needed, and never commit `.env`, `.local/`, dlt secrets, R2 tokens, or GitHub tokens.

## Environment

```bash
task setup
cp .env.example .env
```

Do not commit `.env` or generated data under `.local/`.

## Checks

```bash
task test
task lint
task typecheck
task validate
```

`task validate` wraps:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

You can still run the underlying `uv` commands directly when Task is unavailable.

## Stack validation

```bash
task validate-stack
```

This calls `tools/validate_stack.py` to validate local Delta, dlt, DuckDB, and Dagster stack assumptions.

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

Export your GitHub token from Proton Pass or another password manager into the current shell without printing it in commands:

```bash
export GITHUB_TOKEN=...
```

Then run bounded bronze ingestion through Taskfile:

```bash
task ingest tenant=sandbox max_repositories=1
```

For a bounded validation run that does not write to the default local data root:

```bash
task ingest tenant=sandbox data_root=/tmp/kabuto-kurage-validation max_repositories=1
```

Underlying script, still available when needed:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox --max-repositories 1
```

## GitHub silver models

After bronze ingestion has produced tenant-scoped Delta tables:

```bash
task silver tenant=sandbox
```

For temporary validation data roots, use the same `data_root` used for bronze ingestion:

```bash
task silver tenant=sandbox data_root=/tmp/kabuto-kurage-validation
```

Underlying script:

```bash
uv run python tools/build_github_silver.py --tenant sandbox
```

## GitHub gold metrics

After silver models exist:

```bash
task gold tenant=sandbox
```

For temporary validation data roots, use the same `data_root` used for bronze and silver:

```bash
task gold tenant=sandbox data_root=/tmp/kabuto-kurage-validation
```

Underlying script:

```bash
uv run python tools/build_github_gold.py --tenant sandbox
```

## Local observability

After bronze/silver/gold tables exist, inspect local freshness, row counts, last-ingested state, and rate-limit status:

```bash
task observe tenant=sandbox
```

Use the same `data_root` as ingestion/transformation commands when inspecting temporary validation data:

```bash
task observe tenant=sandbox data_root=/tmp/kabuto-kurage-validation
```

Underlying script:

```bash
uv run python tools/observe_github.py --tenant sandbox --format table
```

## Dagster

```bash
task dagster
```

The Dagster code location exposes six tenant-partitioned GitHub assets:

- `github_bronze_repositories`
- `github_bronze_pull_requests`
- `github_silver_repositories`
- `github_silver_pull_requests`
- `github_gold_pr_throughput_daily`
- `github_gold_pr_cycle_time`

Set `GITHUB_TOKEN` or `GH_TOKEN`, choose a tenant partition such as `sandbox`, and materialize the graph from the UI. For safe demos, set `KABUTO_GITHUB_MAX_REPOSITORIES=1` before starting Dagster.

CLI materialization equivalent through Taskfile:

```bash
export KABUTO_GITHUB_MAX_REPOSITORIES=1
task materialize tenant=sandbox
```

Dagster materializations include local operational metadata such as `observed_row_count`, `freshness_status`, `freshness_lag_hours`, `latest_successful_ingestion_at`, `latest_ingestion_run_id`, and bronze rate-limit fields.

See `docs/dagster-asset-graph.md` for asset metadata and graph details. See `docs/observability.md` for the local freshness command and stale/failed ingestion interpretation.

## REST API and MCP

After gold metrics exist, configure local export API tokens through environment variables or ignored config, then run:

```bash
task api
```

For the MCP metrics wrapper:

```bash
task mcp
```

Both surfaces share the same tenant-scoped query/auth layer. Do not put token values in committed docs or config.
