Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/specs/github-portfolio-scale-demo.md, .loom/decisions/github-scale-demo-many-tenant-opt-in.md

# Curate GitHub Scale Repository Corpus

## Scope

Create the candidate repository corpus for `config/tenants.scale.yaml`.

The corpus should include roughly 20-30 tenant partitions and 45-60 public repositories across at least 24 distinct owners/orgs where practical. It should mix open-source stack projects and broader engineering org projects.

This ticket is research/curation only. Do not add the config file in this ticket unless the parent explicitly merges the work into implementation. Produce a proposed tenant/repository table and evidence for why the list is safe and useful.

## Candidate Categories

Include a curated mix from areas such as:

- orchestration/data platforms: Dagster, Airflow, dbt, dlt;
- analytical engines/storage: DuckDB, Delta, Polars, Apache Arrow/Iceberg/DataFusion;
- API/product engineering: FastAPI, Pydantic, Starlette, Uvicorn;
- observability/infra: Grafana, Prometheus, OpenTelemetry, Kubernetes-adjacent tooling;
- broad engineering orgs with meaningful PR activity and public repos.

Avoid repos that are likely to dominate API usage or runtime without adding portfolio value.

## Current State

Done. A YAML-ready portfolio-scale corpus has been curated and recorded in `.loom/evidence/2026-06-19-github-scale-corpus-curation.md`.

Summary:

- Tenant partitions: 25
- Repositories: 50
- Distinct owners/orgs: 42
- Metadata/access errors: 0
- Private/archived/disabled accepted repos: 0
- Final observed GitHub core rate-limit remaining after checks: 4948 of 5000

The exact YAML-ready tenant/repository list is in the evidence record under `## YAML-Ready Tenant/Repository List`.

## Proposed Tenant Summary

| Tenant | Repositories |
| --- | --- |
| `oss_analytics_engines` | `duckdb/duckdb`, `ClickHouse/ClickHouse` |
| `oss_api_frameworks` | `fastapi/fastapi`, `pallets/flask` |
| `oss_asgi_stack` | `encode/starlette`, `encode/uvicorn` |
| `oss_ci_cd` | `jenkinsci/jenkins`, `go-task/task` |
| `oss_columnar` | `apache/arrow`, `pola-rs/polars` |
| `oss_data_apps` | `apache/superset`, `metabase/metabase` |
| `oss_datastores` | `redis/redis`, `timescale/timescaledb` |
| `oss_delivery` | `argoproj/argo-cd`, `fluxcd/flux2` |
| `oss_developer_tools` | `jupyterlab/jupyterlab`, `mkdocs/mkdocs` |
| `oss_frontend_platforms` | `vitejs/vite`, `vercel/next.js` |
| `oss_iac` | `hashicorp/terraform`, `pulumi/pulumi` |
| `oss_ingestion` | `dlt-hub/dlt`, `meltano/meltano` |
| `oss_kubernetes_tooling` | `kubernetes-sigs/kind`, `helm/helm` |
| `oss_lakehouse` | `delta-io/delta-rs`, `apache/iceberg` |
| `oss_languages` | `python/cpython`, `rust-lang/rust` |
| `oss_ml_apps` | `mlflow/mlflow`, `streamlit/streamlit` |
| `oss_observability` | `grafana/grafana`, `prometheus/prometheus` |
| `oss_orchestration` | `dagster-io/dagster`, `apache/airflow` |
| `oss_python_data` | `pandas-dev/pandas`, `numpy/numpy` |
| `oss_streaming` | `apache/kafka`, `apache/flink` |
| `oss_task_queues` | `celery/celery`, `temporalio/temporal` |
| `oss_telemetry` | `open-telemetry/opentelemetry-collector`, `open-telemetry/opentelemetry-python` |
| `oss_transformation` | `dbt-labs/dbt-core`, `sqlalchemy/sqlalchemy` |
| `oss_validation_clients` | `pydantic/pydantic`, `encode/httpx` |
| `oss_vector_data` | `qdrant/qdrant`, `chroma-core/chroma` |

## Acceptance Criteria

- Proposed corpus contains 20-30 tenant IDs and 45-60 `owner/repo` entries.
- Proposed corpus has at least 24 distinct owners/orgs, or explains why the final number is lower.
- Every repository is public and reachable via GitHub API metadata check using the local PAT from Proton Pass without printing the token.
- For each repo, capture non-secret metadata relevant to curation: private/archive status, default branch, approximate open issue count, and a rough recent-activity signal if available.
- Repositories with obvious risk are removed or marked as deferred with reasons.
- Output includes the exact YAML-ready tenant/repo list for the implementation ticket.
- Record evidence under `.loom/evidence/` with the metadata check results and limits.

## Progress and Notes

- 2026-06-19: Opened as first child of the portfolio-scale plan.
- 2026-06-19: Set active and began corpus curation against `.loom/specs/github-portfolio-scale-demo.md` and `.loom/decisions/github-scale-demo-many-tenant-opt-in.md`.
- 2026-06-19: Selected a 25-tenant / 50-repository candidate corpus mixing data/orchestration stack projects and broader engineering org projects.
- 2026-06-19: Used the Proton Pass item `GitHub API Token`, field `API Key`, only as a local bearer token for GitHub metadata and PR sample checks. The token was not printed or recorded.
- 2026-06-19: Recorded metadata evidence in `.loom/evidence/2026-06-19-github-scale-corpus-curation.md`.
- 2026-06-19: Closed as done because all acceptance criteria are met.

## Results

Acceptance criteria satisfied:

- Corpus has 25 tenant IDs, which is within the 20-30 target.
- Corpus has 50 repositories, which is within the 45-60 target.
- Corpus has 42 distinct owners/orgs, exceeding the 24-owner target.
- Every proposed repository returned HTTP 200 for GitHub metadata and pull-request sample endpoints.
- Evidence captured non-secret metadata for every repo: status, private/archive/disabled flags, default branch, open issue count, stars, repo updated/pushed timestamps, latest sampled PR updated timestamp, and recent sampled PR count in the 180-day window.
- No repositories were deferred after checks; all accepted repos were public, reachable, not archived, not disabled, and recently active in the sampled PR endpoint.
- Exact YAML-ready list is present in `.loom/evidence/2026-06-19-github-scale-corpus-curation.md`.

## Blockers

None.
