# Tenant-Scoped Engineering Metrics Export Surfaces

The local export layer exposes existing GitHub **gold** metrics through REST endpoints
under `/api/v1` and a minimal MCP wrapper over the same query/auth layer. It is a
portfolio learning surface inspired by public Jellyfish API/export and MCP evidence,
not a compatible Jellyfish API/MCP server and not a claim about Jellyfish internals.

## What this API is, and is not

These REST and MCP surfaces demonstrate the customer-facing export concerns that sit after a modeled
lakehouse pipeline:

- expose curated metrics outside Dagster;
- require explicit tenant scope in every path;
- authorize each bearer token against a tenant allowlist;
- return only gold metric fields, never bronze `payload_json` or local secrets;
- keep API behavior small enough to validate deterministically in local tests.

Public Jellyfish research shows API/export and MCP-shaped surfaces for engineering
metrics. This project uses that as inspiration only. These endpoints and tools are
**not** Jellyfish-compatible endpoints/tools, these metrics are **not** Jellyfish
proprietary metrics, and this repository does **not** claim Jellyfish uses FastAPI,
the Python MCP SDK, this tenant model, Delta Lake, Dagster, or these paths/tools
internally.

## Run locally

Install dependencies and materialize gold metrics first. A typical local path is:

```bash
uv sync
export KABUTO_TENANTS_CONFIG=config/tenants.local.yaml
export GITHUB_TOKEN=...              # or GH_TOKEN; needed only for live GitHub ingestion
export KABUTO_GITHUB_MAX_REPOSITORIES=1
uv run dagster asset materialize \
  -m kabuto_kurage.definitions \
  --partition sandbox \
  --select github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests,github_gold_pr_throughput_daily,github_gold_pr_cycle_time
```

Then configure a local API token and start the REST API:

```bash
export KABUTO_API_TOKENS_JSON='{"local-sandbox-token":["sandbox"]}'
uv run uvicorn kabuto_kurage.api.app:app --reload
```

For a committed-secret-free config file, store token values in environment variables
and point the API at a local ignored YAML file:

```yaml
# .local/api-tokens.yaml
tokens:
  - token_env: SANDBOX_EXPORT_API_TOKEN
    tenant_ids:
      - sandbox
```

```bash
export SANDBOX_EXPORT_API_TOKEN='replace-with-local-token'
export KABUTO_API_TOKENS_CONFIG=.local/api-tokens.yaml
uv run uvicorn kabuto_kurage.api.app:app --reload
```

Every metric REST request must include `Authorization: Bearer <token>`. Each MCP tool
call must include the same token value as its explicit `api_token` argument. Each token
maps to an explicit tenant allowlist. The export layer never defaults to all tenants.

## REST endpoint and MCP tool map

| REST endpoint | MCP tool | Gold metric input | Source code constant | Purpose |
| --- | --- | --- | --- | --- |
| `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily` | `github_pr_throughput_daily` | `gold/github/pr_throughput_daily` | `PR_THROUGHPUT_DAILY_TABLE` | Daily PR opened/merged/closed counts by tenant, repository, and date. |
| `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time` | `github_pr_cycle_time` | `gold/github/pr_cycle_time` | `PR_CYCLE_TIME_TABLE` | Per-PR open-to-merge cycle time rows. |
| `GET /api/v1/tenants/{tenant_id}/metrics/github/summary` | `github_metrics_summary` | `gold/github/pr_throughput_daily` and `gold/github/pr_cycle_time` | both constants | Compact demo summary aggregated from existing gold tables. |

The REST API reads through the shared DuckDB query layer in
`src/kabuto_kurage/queries/github_metrics.py`. That layer uses DuckDB SQL and
`delta_scan(...)` against tenant-scoped gold Delta tables instead of loading full
metric tables into Python for filtering. The MCP wrapper in
`src/kabuto_kurage/mcp_server.py` uses the same query layer and auth helper. Neither
surface reads bronze tables, raw GitHub payload JSON, or GitHub token configuration.

## Tenant-scoped access contract

- `tenant_id` is always required in the path.
- `tenant_id` must pass the same validation rules as the lakehouse pipeline.
- `Authorization: Bearer <token>` is required on every REST metric endpoint.
- `api_token` is required on every MCP metric tool.
- Token values are configured outside git through `KABUTO_API_TOKENS_JSON` or an
  ignored file referenced by `KABUTO_API_TOKENS_CONFIG`.
- Each token maps to a non-empty allowlist of tenant IDs.
- A valid token can read only tenants in its allowlist.
- No endpoint or tool supports implicit all-tenant export.
- Cross-tenant exports, admin APIs, OAuth/SSO, and public hosting are out of scope
  for this local milestone.

## Endpoints

### PR throughput daily

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily
```

Query parameters:

- `start_date`: optional `YYYY-MM-DD`, inclusive filter on `metric_date`.
- `end_date`: optional `YYYY-MM-DD`, inclusive filter on `metric_date`.
- `repository_full_name`: optional repeatable repository filter.
- `limit`: optional positive integer, default `100`, maximum `1000`.
- `offset`: optional non-negative integer, default `0`.

Example request:

```bash
curl -H "Authorization: Bearer $SANDBOX_EXPORT_API_TOKEN" \
  'http://127.0.0.1:8000/api/v1/tenants/sandbox/metrics/github/pr-throughput-daily?start_date=2026-06-01&end_date=2026-06-02&repository_full_name=octocat/Hello-World&limit=1&offset=1'
```

Example response:

```json
[
  {
    "tenant_id": "sandbox",
    "repository_full_name": "octocat/Hello-World",
    "metric_date": "2026-06-02",
    "opened_count": 0,
    "merged_count": 1,
    "closed_count": 1,
    "observed_pull_request_count": 1,
    "latest_fetched_at": "2026-06-18T12:00:00+00:00",
    "latest_ingestion_run_id": "run-sandbox"
  }
]
```

### PR cycle time

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time
```

Query parameters:

- `start_date`: optional `YYYY-MM-DD`, inclusive filter on `created_at`.
- `end_date`: optional `YYYY-MM-DD`, inclusive filter on `created_at`.
- `repository_full_name`: optional repeatable repository filter.
- `merged`: optional boolean filter.
- `limit`: optional positive integer, default `100`, maximum `1000`.
- `offset`: optional non-negative integer, default `0`.

Example request:

```bash
curl -H "Authorization: Bearer $SANDBOX_EXPORT_API_TOKEN" \
  'http://127.0.0.1:8000/api/v1/tenants/sandbox/metrics/github/pr-cycle-time?start_date=2026-06-01&end_date=2026-06-03&repository_full_name=octocat/Hello-World&merged=true&limit=2&offset=0'
```

Example response:

```json
[
  {
    "tenant_id": "sandbox",
    "repository_full_name": "octocat/Hello-World",
    "repository_owner": "octocat",
    "pull_request_id": 1,
    "pull_request_node_id": "pr-node-sandbox-1",
    "number": 1,
    "title": "PR 1",
    "user_login": "octocat",
    "state": "closed",
    "merged": true,
    "created_at": "2026-06-01T10:00:00+00:00",
    "merged_at": "2026-06-02T10:00:00+00:00",
    "cycle_time_hours": 24.0,
    "cycle_time_days": 1.0,
    "fetched_at": "2026-06-18T12:00:00+00:00",
    "ingestion_run_id": "run-sandbox"
  }
]
```

### GitHub metrics summary

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/summary
```

Query parameters:

- `start_date`: optional `YYYY-MM-DD`.
- `end_date`: optional `YYYY-MM-DD`.
- `repository_full_name`: optional repeatable repository filter.

Example request:

```bash
curl -H "Authorization: Bearer $SANDBOX_EXPORT_API_TOKEN" \
  'http://127.0.0.1:8000/api/v1/tenants/sandbox/metrics/github/summary?start_date=2026-06-01&end_date=2026-06-03&repository_full_name=octocat/Hello-World'
```

Example response:

```json
{
  "tenant_id": "sandbox",
  "repositories_observed": 1,
  "opened_count": 2,
  "merged_count": 1,
  "closed_count": 1,
  "pull_requests_observed": 3,
  "merged_pull_requests_observed": 2,
  "average_cycle_time_hours": 30.0,
  "latest_fetched_at": "2026-06-18T12:00:00+00:00"
}
```

`average_cycle_time_hours` is a simple local demo aggregate over PR rows that have a
cycle-time value. It is intentionally not presented as a proprietary Jellyfish metric.

## MCP wrapper

The MCP wrapper is intentionally narrow. It exposes **only** these initial tools:

- `github_pr_throughput_daily`
- `github_pr_cycle_time`
- `github_metrics_summary`

Run it locally over stdio after configuring the same token allowlist used by REST:

```bash
export KABUTO_API_TOKENS_JSON='{"local-sandbox-token":["sandbox"]}'
uv run python -m kabuto_kurage.mcp_server
```

Tool inputs map directly to the REST/query contract:

- `tenant_id` is required for every tool.
- `api_token` is required for every tool and is checked through the same
  token-to-tenant allowlist code as REST.
- `start_date`, `end_date`, repeatable/list-like `repository_full_name`, `limit`,
  `offset`, and `merged` match the corresponding REST/query filters where applicable.

Example MCP tool arguments for `github_metrics_summary`:

```json
{
  "tenant_id": "sandbox",
  "api_token": "local-sandbox-token",
  "start_date": "2026-06-01",
  "end_date": "2026-06-03",
  "repository_full_name": "octocat/Hello-World"
}
```

The tool response uses the same JSON shape as the REST summary response. Token values
are used only for local authorization and are not returned. The wrapper is a local
learning analogue to Jellyfish's public MCP pattern, not a clone of Jellyfish's MCP
implementation and not a Jellyfish-compatible MCP server.

## Error responses

REST auth and query-layer errors use predictable JSON envelopes:

```json
{"detail":{"error":"unauthorized","message":"Invalid bearer token"}}
```

Expected REST status codes:

| Status | Meaning | Example |
| --- | --- | --- |
| `401` | Missing, malformed, or invalid bearer token. | `{"detail":{"error":"unauthorized","message":"Missing Authorization bearer token"}}` |
| `403` | Valid token requested a tenant outside its allowlist. | `{"detail":{"error":"forbidden","message":"Token is not allowed to access tenant sandbox"}}` |
| `400` | Invalid tenant ID or query filter error. | `{"detail":{"error":"query_error","message":"end_date must be greater than or equal to start_date"}}` |
| `404` | Requested tenant gold Delta table does not exist. | `{"detail":{"error":"query_error","message":"Gold GitHub pr_cycle_time table does not exist for tenant sandbox: ..."}}` |
| `500` | Local API token configuration is malformed. | `{"detail":{"error":"auth_config_error","message":"API token config must contain a tokens list"}}` |

## Validation coverage

Deterministic tests in `tests/test_export_rest_api.py` and
`tests/test_export_mcp_wrapper.py` seed fixture-backed Delta gold tables and verify:

- the app imports and `/healthz` responds;
- all three metric endpoints return JSON from existing gold tables;
- missing token and invalid token requests return `401`;
- a valid token outside the requested tenant allowlist returns `403`;
- a tenant token cannot read another tenant's gold rows;
- ignored config files can reference token environment variables;
- invalid date ranges map to predictable query errors;
- responses do not include bronze `payload_json`, token fields, or raw `source` fields;
- the MCP server exposes only `github_pr_throughput_daily`, `github_pr_cycle_time`, and
  `github_metrics_summary`;
- MCP tool schemas require explicit `tenant_id` and `api_token`;
- MCP allowed, missing-token, invalid-token, and disallowed-tenant behavior matches the
  same local allowlist semantics as REST.

Run the full validation suite with:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```
