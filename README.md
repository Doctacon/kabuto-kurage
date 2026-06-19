# kabuto-kurage

<img src="images/kabuto-kurage.png" width="300" />

`kabuto-kurage` is a local, open-source-first portfolio data platform for learning the infrastructure and data-engineering patterns behind engineering intelligence products.

It demonstrates a small but coherent data platform:

```text
GitHub API
  └─ repos + pull requests, pagination, rate-limit metadata
      ▼
Bronze Delta Lake
  └─ tenant-scoped raw payload_json + ingestion metadata
      ▼
Silver Delta Lake
  └─ typed repository and pull-request models
      ▼
Gold Delta Lake
  └─ PR throughput and open-to-merge cycle-time metrics
      ▼
Dagster UI
  └─ tenant partitions, asset lineage, materializations, freshness metadata
```

The project is inspired by public Jellyfish Staff Data Engineer role/product research, but it does **not** claim to reproduce Jellyfish's private architecture or proprietary metrics. See [Jellyfish relevance](#jellyfish-relevance-verified-facts-vs-assumptions).

## What a reviewer should notice in five minutes

- **Third-party integration:** real GitHub REST API ingestion using `httpx`, with explicit pagination and rate-limit capture.
- **Lakehouse layers:** bronze raw payloads, silver typed models, and gold metric tables stored as local Delta Lake tables.
- **Multi-tenancy:** two example tenants, tenant-scoped paths, `tenant_id` columns, and tests that fail closed on cross-tenant contamination.
- **Orchestration:** Dagster exposes six tenant-partitioned assets and is the first user-facing surface.
- **Metrics:** daily PR throughput and per-PR open-to-merge cycle time.
- **Observability:** local freshness/row-count/rate-limit CLI plus Dagster materialization metadata.
- **IaC:** Terraform local provider prepares ignored runtime files; optional Docker Compose runs Dagster locally.
- **Validation:** deterministic tests do not require live GitHub credentials.

Start with [`docs/architecture.md`](docs/architecture.md) for the full architecture tour.

## Current implemented milestone

Implemented now:

- Python 3.11+ project managed with `uv`.
- Validated stack: `deltalake`, `pyarrow`, `dagster`, `httpx`.
- Tenant/source configuration in `config/tenants.example.yaml`.
- GitHub repositories and pull requests ingested into tenant-scoped bronze Delta tables.
- Silver repository and pull-request models materialized from bronze Delta tables.
- Gold metrics for daily PR throughput and PR open-to-merge cycle time.
- Dagster asset graph with tenant partitions:
  - `github_bronze_repositories`
  - `github_bronze_pull_requests`
  - `github_silver_repositories`
  - `github_silver_pull_requests`
  - `github_gold_pr_throughput_daily`
  - `github_gold_pr_cycle_time`
- Local observability for row counts, last successful ingestion, freshness/lag, and GitHub rate-limit status.
- Local Infrastructure as Code under `iac/local/`.

Not implemented yet: Jira/CI/CD/incident integrations, webhook queues/sensors, export REST API, MCP wrapper, dashboard, production auth/security, or cloud deployment.

## Prerequisites

Minimum local path:

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/)

Optional local infrastructure path:

- Terraform CLI
- Docker + `docker-compose` or `docker compose`

Live GitHub materialization requires a GitHub token in `GITHUB_TOKEN` or `GH_TOKEN`. Tests do not require a token.

## Quickstart: deterministic local validation

From a fresh checkout:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
```

Expected current test shape: the suite covers stack/scaffold behavior, tenant config, GitHub bronze ingestion, silver models, gold metrics, Dagster assets, observability, local IaC, and tenant isolation.

## Quickstart: configure a bounded GitHub demo

Copy optional local config files:

```bash
cp .env.example .env
cp config/tenants.example.yaml config/tenants.local.yaml
```

Edit `config/tenants.local.yaml` if you want different GitHub owners/repositories. Then export local settings:

```bash
export KABUTO_TENANTS_CONFIG=config/tenants.local.yaml
export GITHUB_TOKEN=...              # or export GH_TOKEN=...
export KABUTO_GITHUB_MAX_REPOSITORIES=1
```

`KABUTO_GITHUB_MAX_REPOSITORIES=1` keeps demos bounded when a tenant config lists an owner with many repositories.

## Run through Dagster UI

Dagster is the first user-facing surface for the project.

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
uv run dagster dev -m kabuto_kurage.definitions
```

Open the URL printed by Dagster. In the asset graph:

1. choose a tenant partition such as `sandbox`;
2. materialize the GitHub bronze assets;
3. materialize downstream silver and gold assets;
4. inspect materialization metadata for row counts, Delta paths, freshness status, ingestion run IDs, and rate-limit fields.

CLI equivalent:

```bash
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests,github_gold_pr_throughput_daily,github_gold_pr_cycle_time
```

See [`docs/dagster-asset-graph.md`](docs/dagster-asset-graph.md).

## Run the pipeline without Dagster

Bronze ingestion:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox --max-repositories 1
```

Silver models:

```bash
uv run python tools/build_github_silver.py --tenant sandbox
```

Gold metrics:

```bash
uv run python tools/build_github_gold.py --tenant sandbox
```

Inspect local operational state:

```bash
uv run python tools/observe_github.py --tenant sandbox --format table
```

For isolated validation, pass the same temporary data root to all commands:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox --data-root /tmp/kabuto-demo --max-repositories 1
uv run python tools/build_github_silver.py --tenant sandbox --data-root /tmp/kabuto-demo
uv run python tools/build_github_gold.py --tenant sandbox --data-root /tmp/kabuto-demo
uv run python tools/observe_github.py --tenant sandbox --data-root /tmp/kabuto-demo --format table
```

## Local Infrastructure as Code

Terraform prepares local runtime files only; it does not provision cloud resources or secrets.

```bash
terraform -chdir=iac/local init
terraform -chdir=iac/local apply
```

Terraform generates ignored files such as:

- `.local/dagster/dagster.yaml`
- `.local/runtime/kabuto.env`
- `.local/data/README.md`

Use generated env values in a shell:

```bash
set -a
source .local/runtime/kabuto.env
set +a
```

Optional Docker Compose Dagster runner:

```bash
export GITHUB_TOKEN=... # optional until materializing live GitHub bronze assets
docker-compose --env-file .local/runtime/kabuto.env -f iac/local/docker-compose.yml up dagster
```

If your environment uses the Compose plugin, replace `docker-compose` with `docker compose`.

See [`docs/local-iac.md`](docs/local-iac.md).

## Local data and secrets

Ignored local paths include:

- `.env` / `.env.*` except `.env.example`
- `config/tenants.local.yaml`
- `.local/`
- `data/`
- `.dagster/`
- `dagster_home/`
- `storage/`
- local SQLite/database files
- Terraform local state/provider cache/plan files

By default, generated data lives under `.local/data`. Override with `KABUTO_DATA_ROOT` when needed.

GitHub token values belong in your shell or ignored `.env`, never in tenant YAML. Tenant YAML stores references like `token_env: GITHUB_TOKEN`.

## Documentation map

| Topic | File |
| --- | --- |
| End-to-end architecture | [`docs/architecture.md`](docs/architecture.md) |
| Development commands | [`docs/development.md`](docs/development.md) |
| Stack validation | [`docs/stack-validation.md`](docs/stack-validation.md) |
| Multi-tenancy model | [`docs/tenancy.md`](docs/tenancy.md) |
| Bronze GitHub ingestion | [`docs/github-bronze-ingestion.md`](docs/github-bronze-ingestion.md) |
| Silver GitHub models | [`docs/github-silver-models.md`](docs/github-silver-models.md) |
| Gold GitHub metrics | [`docs/github-gold-metrics.md`](docs/github-gold-metrics.md) |
| Dagster asset graph | [`docs/dagster-asset-graph.md`](docs/dagster-asset-graph.md) |
| Observability/freshness | [`docs/observability.md`](docs/observability.md) |
| Local IaC | [`docs/local-iac.md`](docs/local-iac.md) |

## Jellyfish relevance: verified facts vs assumptions

Public research is recorded in `.loom/research/2026-06-18-jellyfish-company-research.md`.

Verified public facts used to shape this project:

- Jellyfish publicly describes itself as a software engineering intelligence / engineering management platform.
- Jellyfish public product pages describe integrations with developer tools including GitHub and Jira.
- The public Staff Data Engineer posting emphasized scalable data pipelines, third-party integrations, Terraform/IaC, workflow orchestration for near-real-time and batch processing, cloud data infrastructure, data export pipelines, and AI/LLM integrations.
- The posting listed Delta Lake / lakehouse architecture as a bonus qualification.
- Jellyfish publicly exposes API/MCP surfaces for engineering metrics and related data.

Not verified by this repository:

- Jellyfish's internal orchestrator.
- Jellyfish's internal warehouse/lakehouse engine.
- Jellyfish's internal queue/broker/eventing system.
- Jellyfish's internal tenant isolation model.
- Whether Delta Lake, Dagster, this exact storage layout, or these exact metric definitions are part of Jellyfish's internal implementation.

This project therefore treats GitHub ingestion, Delta Lake, Dagster, Terraform, and tenant-scoped metrics as relevant learning targets—not as claims about Jellyfish's private implementation.

## Project memory

Durable project context lives under `.loom/`:

- `.loom/specs/mini-engineering-intelligence-platform.md`
- `.loom/decisions/initial-portfolio-architecture.md`
- `.loom/research/2026-06-18-jellyfish-company-research.md`
- `.loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md`
