Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md, .loom/specs/github-portfolio-scale-demo.md

# GitHub Scale Repository Corpus Metadata Evidence

## What Was Observed

A candidate opt-in portfolio-scale GitHub corpus was checked through the GitHub REST API using the Proton Pass item `GitHub API Token`, field `API Key`, as a local bearer token. The token value was not printed and is not recorded here.

Summary:

- Generated at: `2026-06-19T22:28:12.389591+00:00`
- Proposed tenant count: `25`
- Proposed repository count: `50`
- Distinct owner/org count: `42`
- First-run history target for later implementation: `180` days
- Final observed GitHub core rate-limit remaining: `4948` of `5000`; used `52`; resource `core`; reset epoch `1781911380`
- Metadata/access errors: `0`
- Archived/private/disabled accepted repos: `0`
- All proposed repos returned HTTP 200 for repository metadata and pull-request sample endpoints.
- Every proposed repo had 30 PRs updated within the first sampled page in the 180-day window, which is enough as a rough recent-activity signal for curation. This is not a full 180-day PR count.

## Procedure

For every candidate `owner/repo`, the curation script called:

```text
GET /repos/{owner}/{repo}
GET /repos/{owner}/{repo}/pulls?state=all&sort=updated&direction=desc&per_page=30
```

The recorded metadata is non-secret: HTTP status, `private`, `archived`, `disabled`, `default_branch`, `open_issues_count`, `stargazers_count`, repo `pushed_at`/`updated_at`, latest sampled PR `updated_at`, count of sampled PRs updated inside the 180-day window, and the final GitHub core rate-limit summary.

## YAML-Ready Tenant/Repository List

```yaml
tenants:
  - tenant_id: oss_analytics_engines
    display_name: OSS Analytics Engines
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - duckdb/duckdb
          - ClickHouse/ClickHouse
  - tenant_id: oss_api_frameworks
    display_name: OSS Api Frameworks
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - fastapi/fastapi
          - pallets/flask
  - tenant_id: oss_asgi_stack
    display_name: OSS Asgi Stack
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - encode/starlette
          - encode/uvicorn
  - tenant_id: oss_ci_cd
    display_name: OSS Ci Cd
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - jenkinsci/jenkins
          - go-task/task
  - tenant_id: oss_columnar
    display_name: OSS Columnar
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - apache/arrow
          - pola-rs/polars
  - tenant_id: oss_data_apps
    display_name: OSS Data Apps
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - apache/superset
          - metabase/metabase
  - tenant_id: oss_datastores
    display_name: OSS Datastores
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - redis/redis
          - timescale/timescaledb
  - tenant_id: oss_delivery
    display_name: OSS Delivery
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - argoproj/argo-cd
          - fluxcd/flux2
  - tenant_id: oss_developer_tools
    display_name: OSS Developer Tools
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - jupyterlab/jupyterlab
          - mkdocs/mkdocs
  - tenant_id: oss_frontend_platforms
    display_name: OSS Frontend Platforms
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - vitejs/vite
          - vercel/next.js
  - tenant_id: oss_iac
    display_name: OSS Iac
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - hashicorp/terraform
          - pulumi/pulumi
  - tenant_id: oss_ingestion
    display_name: OSS Ingestion
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - dlt-hub/dlt
          - meltano/meltano
  - tenant_id: oss_kubernetes_tooling
    display_name: OSS Kubernetes Tooling
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - kubernetes-sigs/kind
          - helm/helm
  - tenant_id: oss_lakehouse
    display_name: OSS Lakehouse
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - delta-io/delta-rs
          - apache/iceberg
  - tenant_id: oss_languages
    display_name: OSS Languages
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - python/cpython
          - rust-lang/rust
  - tenant_id: oss_ml_apps
    display_name: OSS Ml Apps
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - mlflow/mlflow
          - streamlit/streamlit
  - tenant_id: oss_observability
    display_name: OSS Observability
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - grafana/grafana
          - prometheus/prometheus
  - tenant_id: oss_orchestration
    display_name: OSS Orchestration
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - dagster-io/dagster
          - apache/airflow
  - tenant_id: oss_python_data
    display_name: OSS Python Data
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - pandas-dev/pandas
          - numpy/numpy
  - tenant_id: oss_streaming
    display_name: OSS Streaming
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - apache/kafka
          - apache/flink
  - tenant_id: oss_task_queues
    display_name: OSS Task Queues
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - celery/celery
          - temporalio/temporal
  - tenant_id: oss_telemetry
    display_name: OSS Telemetry
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - open-telemetry/opentelemetry-collector
          - open-telemetry/opentelemetry-python
  - tenant_id: oss_transformation
    display_name: OSS Transformation
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - dbt-labs/dbt-core
          - sqlalchemy/sqlalchemy
  - tenant_id: oss_validation_clients
    display_name: OSS Validation Clients
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - pydantic/pydantic
          - encode/httpx
  - tenant_id: oss_vector_data
    display_name: OSS Vector Data
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - qdrant/qdrant
          - chroma-core/chroma
```

## Metadata Results

| Tenant | Repository | Metadata | Pulls | Private | Archived | Default branch | Open issues | Stars | Repo updated | Latest sampled PR update | Recent sampled PRs in 180d |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: | --- | --- | ---: |
| `oss_orchestration` | `dagster-io/dagster` | 200 | 200 | false | false | `master` | 2654 | 15722 | `2026-06-19T20:37:43Z` | `2026-06-19T21:16:55Z` | 30 / 30 |
| `oss_orchestration` | `apache/airflow` | 200 | 200 | false | false | `main` | 1706 | 45871 | `2026-06-19T18:58:44Z` | `2026-06-19T22:24:58Z` | 30 / 30 |
| `oss_ingestion` | `dlt-hub/dlt` | 200 | 200 | false | false | `devel` | 354 | 5497 | `2026-06-19T17:58:28Z` | `2026-06-19T19:31:26Z` | 30 / 30 |
| `oss_ingestion` | `meltano/meltano` | 200 | 200 | false | false | `main` | 163 | 2538 | `2026-06-19T21:52:10Z` | `2026-06-19T21:52:21Z` | 30 / 30 |
| `oss_transformation` | `dbt-labs/dbt-core` | 200 | 200 | false | false | `main` | 1458 | 13035 | `2026-06-19T21:23:58Z` | `2026-06-19T21:47:00Z` | 30 / 30 |
| `oss_transformation` | `sqlalchemy/sqlalchemy` | 200 | 200 | false | false | `main` | 209 | 11924 | `2026-06-19T16:26:43Z` | `2026-06-18T18:13:07Z` | 30 / 30 |
| `oss_lakehouse` | `delta-io/delta-rs` | 200 | 200 | false | false | `main` | 201 | 3243 | `2026-06-19T02:21:29Z` | `2026-06-19T22:00:13Z` | 30 / 30 |
| `oss_lakehouse` | `apache/iceberg` | 200 | 200 | false | false | `main` | 758 | 8978 | `2026-06-19T20:28:00Z` | `2026-06-19T22:19:04Z` | 30 / 30 |
| `oss_columnar` | `apache/arrow` | 200 | 200 | false | false | `main` | 2647 | 16855 | `2026-06-19T22:15:03Z` | `2026-06-19T19:08:01Z` | 30 / 30 |
| `oss_columnar` | `pola-rs/polars` | 200 | 200 | false | false | `main` | 2805 | 38829 | `2026-06-19T19:49:02Z` | `2026-06-19T21:55:49Z` | 30 / 30 |
| `oss_analytics_engines` | `duckdb/duckdb` | 200 | 200 | false | false | `main` | 554 | 38891 | `2026-06-19T22:19:03Z` | `2026-06-19T20:29:12Z` | 30 / 30 |
| `oss_analytics_engines` | `ClickHouse/ClickHouse` | 200 | 200 | false | false | `master` | 6176 | 48140 | `2026-06-19T22:13:41Z` | `2026-06-19T22:25:37Z` | 30 / 30 |
| `oss_python_data` | `pandas-dev/pandas` | 200 | 200 | false | false | `main` | 3171 | 49014 | `2026-06-19T21:15:10Z` | `2026-06-19T21:15:13Z` | 30 / 30 |
| `oss_python_data` | `numpy/numpy` | 200 | 200 | false | false | `main` | 2395 | 32218 | `2026-06-19T22:25:08Z` | `2026-06-19T22:23:32Z` | 30 / 30 |
| `oss_api_frameworks` | `fastapi/fastapi` | 200 | 200 | false | false | `master` | 87 | 99408 | `2026-06-19T21:40:30Z` | `2026-06-19T20:36:50Z` | 30 / 30 |
| `oss_api_frameworks` | `pallets/flask` | 200 | 200 | false | false | `main` | 4 | 71680 | `2026-06-19T21:40:08Z` | `2026-06-17T12:46:31Z` | 30 / 30 |
| `oss_asgi_stack` | `encode/starlette` | 200 | 200 | false | false | `main` | 45 | 12408 | `2026-06-19T19:10:48Z` | `2026-06-19T00:03:58Z` | 30 / 30 |
| `oss_asgi_stack` | `encode/uvicorn` | 200 | 200 | false | false | `main` | 71 | 10771 | `2026-06-19T18:12:41Z` | `2026-06-18T18:50:19Z` | 30 / 30 |
| `oss_validation_clients` | `pydantic/pydantic` | 200 | 200 | false | false | `main` | 569 | 28060 | `2026-06-19T20:44:12Z` | `2026-06-19T20:17:41Z` | 30 / 30 |
| `oss_validation_clients` | `encode/httpx` | 200 | 200 | false | false | `master` | 145 | 15302 | `2026-06-19T20:55:49Z` | `2026-05-26T10:22:59Z` | 30 / 30 |
| `oss_observability` | `grafana/grafana` | 200 | 200 | false | false | `main` | 3600 | 74530 | `2026-06-19T22:18:44Z` | `2026-06-19T21:44:00Z` | 30 / 30 |
| `oss_observability` | `prometheus/prometheus` | 200 | 200 | false | false | `main` | 848 | 64624 | `2026-06-19T22:18:48Z` | `2026-06-19T21:01:46Z` | 30 / 30 |
| `oss_telemetry` | `open-telemetry/opentelemetry-collector` | 200 | 200 | false | false | `main` | 695 | 7146 | `2026-06-19T15:30:29Z` | `2026-06-19T20:44:16Z` | 30 / 30 |
| `oss_telemetry` | `open-telemetry/opentelemetry-python` | 200 | 200 | false | false | `main` | 420 | 2498 | `2026-06-19T15:51:07Z` | `2026-06-19T21:56:34Z` | 30 / 30 |
| `oss_iac` | `hashicorp/terraform` | 200 | 200 | false | false | `main` | 1914 | 48742 | `2026-06-19T22:10:46Z` | `2026-06-19T20:21:26Z` | 30 / 30 |
| `oss_iac` | `pulumi/pulumi` | 200 | 200 | false | false | `master` | 2468 | 25330 | `2026-06-19T19:55:11Z` | `2026-06-19T16:46:25Z` | 30 / 30 |
| `oss_delivery` | `argoproj/argo-cd` | 200 | 200 | false | false | `master` | 4213 | 23184 | `2026-06-19T21:34:01Z` | `2026-06-19T21:03:14Z` | 30 / 30 |
| `oss_delivery` | `fluxcd/flux2` | 200 | 200 | false | false | `main` | 252 | 8205 | `2026-06-19T17:52:20Z` | `2026-06-19T17:52:59Z` | 30 / 30 |
| `oss_kubernetes_tooling` | `kubernetes-sigs/kind` | 200 | 200 | false | false | `main` | 224 | 15311 | `2026-06-19T20:26:15Z` | `2026-06-19T18:00:24Z` | 30 / 30 |
| `oss_kubernetes_tooling` | `helm/helm` | 200 | 200 | false | false | `main` | 402 | 29891 | `2026-06-19T04:04:38Z` | `2026-06-19T21:38:31Z` | 30 / 30 |
| `oss_data_apps` | `apache/superset` | 200 | 200 | false | false | `master` | 1003 | 73381 | `2026-06-19T22:21:43Z` | `2026-06-19T22:26:36Z` | 30 / 30 |
| `oss_data_apps` | `metabase/metabase` | 200 | 200 | false | false | `master` | 4064 | 47733 | `2026-06-19T22:08:00Z` | `2026-06-19T22:24:29Z` | 30 / 30 |
| `oss_ml_apps` | `mlflow/mlflow` | 200 | 200 | false | false | `master` | 1989 | 26634 | `2026-06-19T20:12:48Z` | `2026-06-19T21:33:53Z` | 30 / 30 |
| `oss_ml_apps` | `streamlit/streamlit` | 200 | 200 | false | false | `develop` | 1303 | 45008 | `2026-06-19T20:36:09Z` | `2026-06-19T21:42:34Z` | 30 / 30 |
| `oss_streaming` | `apache/kafka` | 200 | 200 | false | false | `trunk` | 439 | 32887 | `2026-06-19T21:40:08Z` | `2026-06-19T21:13:58Z` | 30 / 30 |
| `oss_streaming` | `apache/flink` | 200 | 200 | false | false | `master` | 343 | 26097 | `2026-06-19T16:09:15Z` | `2026-06-19T22:26:00Z` | 30 / 30 |
| `oss_datastores` | `redis/redis` | 200 | 200 | false | false | `unstable` | 2853 | 74989 | `2026-06-19T21:54:42Z` | `2026-06-19T12:44:33Z` | 30 / 30 |
| `oss_datastores` | `timescale/timescaledb` | 200 | 200 | false | false | `main` | 384 | 22934 | `2026-06-19T21:27:14Z` | `2026-06-19T21:22:18Z` | 30 / 30 |
| `oss_vector_data` | `qdrant/qdrant` | 200 | 200 | false | false | `master` | 582 | 32468 | `2026-06-19T20:24:49Z` | `2026-06-19T21:33:08Z` | 30 / 30 |
| `oss_vector_data` | `chroma-core/chroma` | 200 | 200 | false | false | `main` | 681 | 28493 | `2026-06-19T20:04:58Z` | `2026-06-19T16:21:01Z` | 30 / 30 |
| `oss_task_queues` | `celery/celery` | 200 | 200 | false | false | `main` | 784 | 28601 | `2026-06-19T22:21:46Z` | `2026-06-19T14:07:18Z` | 30 / 30 |
| `oss_task_queues` | `temporalio/temporal` | 200 | 200 | false | false | `main` | 780 | 21091 | `2026-06-19T21:22:03Z` | `2026-06-19T22:26:33Z` | 30 / 30 |
| `oss_languages` | `python/cpython` | 200 | 200 | false | false | `main` | 9322 | 73323 | `2026-06-19T21:43:56Z` | `2026-06-19T22:27:33Z` | 30 / 30 |
| `oss_languages` | `rust-lang/rust` | 200 | 200 | false | false | `main` | 12462 | 113968 | `2026-06-19T22:07:38Z` | `2026-06-19T22:22:31Z` | 30 / 30 |
| `oss_frontend_platforms` | `vitejs/vite` | 200 | 200 | false | false | `main` | 731 | 81549 | `2026-06-19T20:31:23Z` | `2026-06-19T17:30:04Z` | 30 / 30 |
| `oss_frontend_platforms` | `vercel/next.js` | 200 | 200 | false | false | `canary` | 4101 | 140088 | `2026-06-19T21:40:04Z` | `2026-06-19T22:16:10Z` | 30 / 30 |
| `oss_ci_cd` | `jenkinsci/jenkins` | 200 | 200 | false | false | `master` | 3602 | 25497 | `2026-06-19T21:36:58Z` | `2026-06-19T21:22:15Z` | 30 / 30 |
| `oss_ci_cd` | `go-task/task` | 200 | 200 | false | false | `main` | 210 | 15734 | `2026-06-19T21:11:11Z` | `2026-06-18T22:03:20Z` | 30 / 30 |
| `oss_developer_tools` | `jupyterlab/jupyterlab` | 200 | 200 | false | false | `main` | 2575 | 15201 | `2026-06-19T16:11:56Z` | `2026-06-19T20:57:29Z` | 30 / 30 |
| `oss_developer_tools` | `mkdocs/mkdocs` | 200 | 200 | false | false | `master` | 183 | 22187 | `2026-06-19T21:10:13Z` | `2026-06-17T07:09:42Z` | 30 / 30 |

## Excluded or Deferred Repositories

No candidate repositories were excluded after metadata checks. All 50 proposed repositories were public, reachable, not archived, not disabled, and had recent PR activity in the sampled first page.

## What This Supports or Challenges

This supports closing `.loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md`: the proposed corpus has 25 tenant partitions, 50 repositories, and 42 distinct owners/orgs, satisfying the requested scale shape and owner diversity target. The evidence also supports the later implementation ticket for `config/tenants.scale.yaml` by providing an exact YAML-ready list.

## Limits

- This is metadata and first-page PR sampling only, not a full materialization or full 180-day PR count.
- Recent sampled PR count is capped at `30` because the sample endpoint used `per_page=30`. It proves recent activity exists but not total volume.
- This evidence does not validate `config/tenants.scale.yaml` because that file is intentionally out of scope for the curation ticket.
- This evidence does not validate future first-run lookback implementation, full Dagster backfills, or downstream metrics row counts.
