# kabuto-kurage

<img src="images/kabuto-kurage.png" width="300" />

`kabuto-kurage` is a local, open-source-first portfolio data platform for learning the infrastructure and data-engineering patterns behind engineering intelligence products.

The target shape is a miniature Jellyfish-inspired platform: GitHub engineering activity flows into Delta Lake, Dagster orchestrates the assets, tenant boundaries are explicit, and later milestones compute delivery/productivity metrics with operational visibility.

## Current milestone

The repository is currently at the **Dagster GitHub asset graph** milestone:

- Python 3.11+ project managed with `uv`.
- Validated core stack: `deltalake`, `pyarrow`, `dagster`, `httpx`.
- Source and test layout are in place.
- Tenant/source configuration is represented in `config/tenants.example.yaml`.
- GitHub repositories and pull requests can be ingested into tenant-scoped bronze Delta tables.
- Stable silver repository and pull request models can be materialized from bronze Delta tables.
- Dagster exposes tenant-partitioned GitHub bronze and silver assets as the first user-facing surface.
- Secrets and generated local data are ignored by git.

Gold metrics are tracked in later Loom tickets under `.loom/tickets/`.

## Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

## Install

```bash
uv sync
```

Optional local secrets/config setup:

```bash
cp .env.example .env
cp config/tenants.example.yaml config/tenants.local.yaml
# Edit .env and config/tenants.local.yaml for local owner/repository choices.
# Set GITHUB_TOKEN or GH_TOKEN before running GitHub ingestion.
```

## Developer commands

Run tests:

```bash
uv run pytest
```

Run lint:

```bash
uv run ruff check .
```

Run type checks:

```bash
uv run mypy src
```

Validate tenant/source configuration in Python:

```bash
uv run python -c "from kabuto_kurage.tenancy import load_tenant_registry; print(load_tenant_registry().tenant_ids)"
```

Start Dagster UI/code location:

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

Dagster will show four tenant-partitioned GitHub assets:

- `github_bronze_repositories`
- `github_bronze_pull_requests`
- `github_silver_repositories`
- `github_silver_pull_requests`

Set `GITHUB_TOKEN` or `GH_TOKEN`, choose a tenant partition such as `sandbox`, and materialize the graph from the UI. For safe local demos, set `KABUTO_GITHUB_MAX_REPOSITORIES=1` before starting Dagster.

Run GitHub bronze ingestion for one tenant:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox
```

For a bounded validation run against a temporary data root:

```bash
uv run python tools/ingest_github_bronze.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation \
  --max-repositories 1
```

Build GitHub silver models from existing bronze tables without Dagster:

```bash
uv run python tools/build_github_silver.py --tenant sandbox
```

Materialize the full GitHub bronze/silver asset graph from the CLI:

```bash
export GITHUB_TOKEN=...
export KABUTO_GITHUB_MAX_REPOSITORIES=1
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests
```

Run the stack validation proof from the previous milestone:

```bash
uv run python tools/validate_stack.py
```

## Local data and secrets

Ignored local paths include:

- `.env` / `.env.*` except `.env.example`
- `.local/`
- `data/`
- `.dagster/`
- `dagster_home/`
- `storage/`
- local SQLite/database files

By default, generated data should live under `.local/data`. Override with `KABUTO_DATA_ROOT` when needed.

Tenant/source configuration is loaded from `KABUTO_TENANTS_CONFIG` when set, otherwise from `config/tenants.example.yaml`. Local overrides should live in ignored `config/tenants.local.yaml`.

See `docs/tenancy.md` for the local tenancy model, storage path convention, and alternatives considered. See `docs/github-bronze-ingestion.md` for GitHub ingestion behavior, pagination/rate-limit notes, bronze columns, and failure semantics. See `docs/github-silver-models.md` for silver table columns, intended use, and schema-evolution notes. See `docs/dagster-asset-graph.md` for Dagster UI, tenant partitions, CLI materialization, and asset metadata.

## Project memory

Durable context lives under `.loom/`:

- `.loom/specs/mini-engineering-intelligence-platform.md`
- `.loom/decisions/initial-portfolio-architecture.md`
- `.loom/research/2026-06-18-jellyfish-company-research.md`
- `.loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md`
