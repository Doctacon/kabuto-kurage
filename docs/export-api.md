# Tenant-Scoped Engineering Metrics REST API

The local export API exposes existing GitHub gold metrics through REST endpoints under
`/api/v1`. It is a portfolio learning surface inspired by public Jellyfish API/export
patterns, not a compatible Jellyfish API and not a claim about Jellyfish internals.

## Run locally

Install dependencies, materialize gold metrics, then run:

```bash
export KABUTO_API_TOKENS_JSON='{"local-sandbox-token":["sandbox"]}'
uv run uvicorn kabuto_kurage.api.app:app --reload
```

For a committed-secret-free config file, store token values in environment variables and
point the API at a local ignored YAML file:

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

Every request must include `Authorization: Bearer <token>`. Each token maps to an
explicit tenant allowlist. The API never defaults to all tenants.

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

Response: a JSON array with `tenant_id`, `repository_full_name`, `metric_date`,
`opened_count`, `merged_count`, `closed_count`, `observed_pull_request_count`,
`latest_fetched_at`, and `latest_ingestion_run_id`.

### PR cycle time

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time
```

Query parameters:

- `start_date`: optional `YYYY-MM-DD`, inclusive filter on `created_at`.
- `end_date`: optional `YYYY-MM-DD`, inclusive filter on `created_at`.
- `repository_full_name`: optional repeatable repository filter.
- `merged`: optional boolean.
- `limit`: optional positive integer, default `100`, maximum `1000`.
- `offset`: optional non-negative integer, default `0`.

Response: a JSON array with tenant-scoped PR cycle-time fields from the gold metric
contract. Raw bronze `payload_json` and token values are not returned.

### GitHub metrics summary

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/summary
```

Query parameters:

- `start_date`: optional `YYYY-MM-DD`.
- `end_date`: optional `YYYY-MM-DD`.
- `repository_full_name`: optional repeatable repository filter.

Response: one JSON object containing `tenant_id`, repository and PR counts, merged PR
count, `average_cycle_time_hours`, and `latest_fetched_at`.

## Error responses

Auth and query-layer errors use predictable JSON envelopes:

```json
{"detail":{"error":"unauthorized","message":"Invalid bearer token"}}
```

Expected status codes:

- `401`: missing, malformed, or invalid bearer token.
- `403`: valid token requested a tenant outside its allowlist.
- `400`: invalid tenant ID or query filter error.
- `404`: requested tenant gold Delta table does not exist.
- `500`: local API token configuration is malformed.

## Examples

```bash
curl -H "Authorization: Bearer $SANDBOX_EXPORT_API_TOKEN" \
  'http://127.0.0.1:8000/api/v1/tenants/sandbox/metrics/github/summary?repository_full_name=octocat/Hello-World'
```
