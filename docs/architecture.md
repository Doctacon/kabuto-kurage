# Architecture Overview

`kabuto-kurage` is a local, portfolio-oriented data platform that demonstrates the core mechanics behind an engineering-intelligence product. It does not claim to reproduce Jellyfish's private architecture or any company's private system.

In one sentence:

> GitHub repository and pull-request activity is ingested per tenant, stored in Delta Lake bronze tables, modeled into silver tables, transformed into gold engineering metrics, orchestrated in Dagster, and inspected with local freshness/observability tooling.

## Five-Minute Map

```text
                         ┌──────────────────────────────┐
                         │ config/tenants.example.yaml  │
                         │ tenant_id + GitHub source    │
                         │ token env var reference only │
                         └──────────────┬───────────────┘
                                        │ tenant partition
                                        ▼
┌──────────────┐   REST API    ┌──────────────────────────┐
│ GitHub API   │──────────────▶│ Bronze Delta tables      │
│ repos + PRs  │               │ raw payload_json +       │
│ pagination   │               │ fetch/run/rate metadata  │
└──────────────┘               └─────────────┬────────────┘
                                             │ normalize stable fields
                                             ▼
                              ┌──────────────────────────┐
                              │ Silver Delta tables      │
                              │ repositories + PR facts  │
                              │ typed nullable columns   │
                              └─────────────┬────────────┘
                                            │ compute product metrics
                                            ▼
                              ┌──────────────────────────┐
                              │ Gold Delta tables        │
                              │ PR throughput daily      │
                              │ PR open-to-merge time    │
                              └─────────────┬────────────┘
                                            │ materializations + metadata
                                            ▼
                              ┌──────────────────────────┐
                              │ Dagster UI               │
                              │ tenant partitions, asset │
                              │ lineage, runs, freshness │
                              └──────────────────────────┘
```

Supporting local platform pieces:

```text
FastAPI export API ───────▶ tenant-scoped `/api/v1` JSON over gold metrics
MCP metric wrapper ───────▶ three tenant-scoped tools over the same query/auth layer
Terraform local provider ──▶ .local/dagster + .local/runtime + .local/data
Docker Compose (optional) ─▶ local Dagster service runner
observe_github.py ────────▶ row counts, freshness, last run, rate-limit status
pytest/ruff/mypy ─────────▶ deterministic validation without live GitHub
```

## Implemented System Boundaries

Implemented now:

- GitHub REST API ingestion for repositories and pull requests.
- Tenant registry and tenant-scoped storage paths.
- Delta Lake bronze/silver/gold tables on the local filesystem.
- Dagster assets partitioned by tenant.
- Gold metrics:
  - daily PR opened/merged/closed counts;
  - per-PR open-to-merge cycle time.
- Local observability command for table existence, row counts, freshness, last run IDs, and GitHub rate-limit metadata.
- Tenant-scoped REST export API over existing gold metrics.
- Minimal MCP wrapper exposing the same existing gold metric contracts as three tools.
- Local Terraform module and optional Docker Compose service runner.

Not implemented yet:

- Jira, CI/CD, incident, review/comment, or AI-tool integrations.
- Customer dashboard or broader MCP/API surface beyond the three initial metric tools.
- Near-real-time webhooks/queues/sensors.
- Production auth, row-level security, encryption, alerting, cloud deployment, or tenant resource isolation.

## Code and Data Layout

| Concern | Location |
| --- | --- |
| Tenant/source config | `config/tenants.example.yaml` |
| Tenant validation and registry | `src/kabuto_kurage/tenancy.py` |
| Local path conventions | `src/kabuto_kurage/paths.py` |
| GitHub bronze ingestion | `src/kabuto_kurage/ingestion/github_bronze.py` |
| Silver transforms | `src/kabuto_kurage/transforms/github_silver.py` |
| Gold metrics | `src/kabuto_kurage/transforms/github_gold.py` |
| Dagster assets | `src/kabuto_kurage/assets/github.py` |
| Dagster code location | `src/kabuto_kurage/definitions.py` |
| REST export API | `src/kabuto_kurage/api/app.py` |
| REST API auth | `src/kabuto_kurage/api/auth.py` |
| MCP metric wrapper | `src/kabuto_kurage/mcp_server.py` |
| Gold metric query layer | `src/kabuto_kurage/queries/github_metrics.py` |
| Local observability | `src/kabuto_kurage/observability.py` |
| Local IaC | `iac/local/` |
| Validation tests | `tests/` |

Delta tables use this local convention:

```text
.local/data/delta/tenants/{tenant_id}/{layer}/github/{table_name}
```

Examples:

```text
.local/data/delta/tenants/sandbox/bronze/github/pull_requests
.local/data/delta/tenants/sandbox/silver/github/pull_requests
.local/data/delta/tenants/sandbox/gold/github/pr_cycle_time
```

## Data Flow

### 1. Tenant/source configuration

Tenant configuration is committed as an example file and can be copied for local edits:

```bash
cp config/tenants.example.yaml config/tenants.local.yaml
export KABUTO_TENANTS_CONFIG=config/tenants.local.yaml
```

The config stores GitHub token **environment variable names**, not token values:

```yaml
token_env: GITHUB_TOKEN
```

The loader rejects invalid tenant IDs, duplicate tenants, missing GitHub source config, invalid repository names, and obvious accidental GitHub token values where an env-var reference belongs.

### 2. Bronze: raw GitHub payloads

Bronze ingestion fetches configured repositories and pull requests via GitHub REST API using `httpx`.

It intentionally keeps integration concerns visible:

- `Link` header pagination;
- `x-ratelimit-*` header capture;
- source URLs and IDs;
- `ingestion_run_id` and `fetched_at`;
- canonical `payload_json` for schema-evolution learning.

This first snapshot-style bronze path overwrites each tenant/resource table after API fetching succeeds. That makes repeated local runs idempotent for the configured scope. It does not yet implement append-only raw history or incremental cursors.

### 3. Silver: stable analytical models

Silver transforms turn raw GitHub payloads into typed, nullable Delta tables:

- `silver/github/repositories`
- `silver/github/pull_requests`

The silver layer preserves `tenant_id`, GitHub IDs/URLs, and bronze lineage columns. Missing or newly added GitHub fields are tolerated by keeping raw payloads in bronze and only promoting fields to silver when downstream analytics need a stable contract.

### 4. Gold: engineering metrics

Gold metrics derive from the silver PR table:

- `gold/github/pr_throughput_daily`
  - grain: tenant + repository + UTC date;
  - counts PRs opened, merged, and closed on each date.
- `gold/github/pr_cycle_time`
  - grain: one row per PR;
  - computes open-to-merge duration in hours and days when timestamps are valid.

These are intentionally simple portfolio metrics. They are not Jellyfish proprietary metrics and should not be interpreted as complete DORA or allocation models.

### 5. Dagster UI

Dagster exposes the flow as six tenant-partitioned assets:

```text
github_bronze_repositories ┐
                           ├─> github_silver_repositories
github_bronze_pull_requests ┘

                           ┌─> github_silver_pull_requests ──> github_gold_pr_throughput_daily
github_bronze_repositories ┤                              └──> github_gold_pr_cycle_time
github_bronze_pull_requests ┘
```

Start the UI:

```bash
export DAGSTER_HOME=.local/dagster
mkdir -p "$DAGSTER_HOME"
export GITHUB_TOKEN=...              # required only for live GitHub bronze materialization
export KABUTO_GITHUB_MAX_REPOSITORIES=1  # recommended for bounded demos
uv run dagster dev -m kabuto_kurage.definitions
```

Open the URL printed by Dagster, select a tenant partition such as `sandbox`, and materialize the graph.

Asset materializations include row counts, tenant/source/layer metadata, Delta table paths and versions, freshness status, latest ingestion timestamps/run IDs, and GitHub rate-limit metadata where available.

### 6. REST export API and MCP wrapper

The REST export API exposes only existing GitHub gold metrics under `/api/v1`:

| Endpoint | Gold metric input |
| --- | --- |
| `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily` | `gold/github/pr_throughput_daily` |
| `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time` | `gold/github/pr_cycle_time` |
| `GET /api/v1/tenants/{tenant_id}/metrics/github/summary` | both gold metric tables |

The API requires `Authorization: Bearer <token>` on every metric endpoint. Token
configuration stays outside git and maps token values to explicit tenant allowlists.
Missing or invalid tokens return `401`; valid tokens requesting a tenant outside their
allowlist return `403`; no endpoint defaults to all tenants.

The MCP wrapper exposes only the matching initial metric tools:

- `github_pr_throughput_daily`
- `github_pr_cycle_time`
- `github_metrics_summary`

Each tool requires explicit `tenant_id` and `api_token` arguments and shares the REST
API's token-to-tenant allowlist logic in `src/kabuto_kurage/api/auth.py`.

These export surfaces are local portfolio analogues to public Jellyfish API/export and
MCP evidence, not Jellyfish-compatible APIs and not a claim that Jellyfish uses these
endpoints, tools, metrics, tenant model, or implementation details internally.

See `docs/export-api.md` for setup, curl/tool examples, response examples, and validation.

## Multi-Tenancy Model

This project uses local logical isolation:

1. Every configured tenant has a validated `tenant_id`.
2. Delta paths include `tenants/{tenant_id}`.
3. Bronze, silver, and gold rows preserve `tenant_id` as a column.
4. Silver and gold materializers fail closed if a tenant-scoped input path contains rows for another tenant.
5. Tests validate that two tenants' bronze/silver/gold rows and metrics stay separate.

This is useful for learning and portfolio evidence, but it is not production security. A real customer-facing system would also need authorization, audit logs, encryption, row-level security or equivalent controls, secret management, deletion/export workflows, and tenant-aware compute/resource isolation.

See `docs/tenancy.md` for details and limitations.

## Delta Lake Learning Notes

The project uses the open-source `deltalake` Python package (`delta-rs`) with `pyarrow`, avoiding a Spark/JVM dependency for the local learning loop.

Concrete Delta concepts visible in the repo:

- each table directory contains `_delta_log/` transaction-log files;
- tests assert Delta logs exist after writes;
- Dagster metadata reports Delta table versions;
- bronze stores raw payload JSON while silver/gold expose stable typed contracts;
- docs explain how new GitHub fields should flow through bronze first, then be promoted to silver only when needed.

Useful files:

- `docs/stack-validation.md`
- `docs/github-bronze-ingestion.md`
- `docs/github-silver-models.md`
- `docs/github-gold-metrics.md`

## Observability

Local observability is intentionally lightweight and inspectable:

```bash
uv run python tools/observe_github.py --tenant sandbox --format table
```

The command reports one row per known GitHub table with:

- table existence;
- row count;
- Delta version;
- latest successful ingestion timestamp;
- latest ingestion run ID;
- freshness lag/status;
- GitHub rate-limit summary for bronze tables.

Dagster materializations expose the same operational signals where relevant.

See `docs/observability.md` for how to interpret `missing`, `empty`, `unknown`, `fresh`, and `stale`.

## Local Infrastructure as Code

The local IaC is deliberately modest and honest:

- Terraform uses only the `hashicorp/local` provider.
- Terraform generates ignored local runtime files under `.local/`.
- Docker Compose optionally runs Dagster from the checkout.
- Neither Terraform nor Compose provisions cloud infrastructure, Kubernetes, managed databases, or secrets.

Prepare runtime files:

```bash
terraform -chdir=iac/local init
terraform -chdir=iac/local apply
```

Optional Compose runner:

```bash
docker-compose --env-file .local/runtime/kabuto.env -f iac/local/docker-compose.yml up dagster
```

See `docs/local-iac.md` for the boundary between Terraform, Docker Compose, and Python/Dagster.

## Jellyfish Relevance: Verified Facts vs Project Assumptions

This section is intentionally conservative. It ties the project to public research without claiming knowledge of Jellyfish's private architecture.

Verified public facts from `.loom/research/2026-06-18-jellyfish-company-research.md`:

- Jellyfish publicly describes itself as a software engineering intelligence / engineering management platform.
- Public product pages describe integrations with developer tools including GitHub and Jira.
- The public Staff Data Engineer posting called out scalable data pipelines, third-party integrations, cloud data infrastructure, Terraform/IaC, workflow orchestration for near-real-time and batch processing, data export pipelines, and AI/LLM integrations.
- The same posting listed Delta Lake / lakehouse experience as a bonus qualification.
- Jellyfish publicly exposes API/MCP surfaces for engineering metrics and related data.

Not verified publicly by this project:

- Jellyfish's internal orchestrator.
- Jellyfish's internal warehouse/lakehouse engine.
- Jellyfish's internal queue/broker/eventing system.
- Jellyfish's internal tenant isolation model.
- Whether Delta Lake, Dagster, this exact storage layout, or these exact metric definitions are part of Jellyfish's internal implementation.

Project assumptions for learning:

- GitHub PR data is a realistic first developer-tool signal to ingest.
- Tenant-scoped lakehouse tables are a useful way to practice multi-tenant data thinking locally.
- Dagster assets are a good way to make orchestration and lineage visible, even though the job posting listed Dagster only as one example among orchestrators.
- Terraform local resources are enough to demonstrate IaC workflow concepts without inventing fake cloud infrastructure.

## Validation Posture

Current validation commands:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
terraform -chdir=iac/local fmt -check
terraform -chdir=iac/local init -backend=false
terraform -chdir=iac/local validate
```

The tests are deterministic and do not require live GitHub. Live GitHub runs require `GITHUB_TOKEN` or `GH_TOKEN` and should usually set `KABUTO_GITHUB_MAX_REPOSITORIES=1` for bounded demos.
