Status: draft
Created: 2026-06-18
Updated: 2026-06-18

# Engineering Metrics Export Surface

## Purpose and Scope

This spec defines the next milestone after the Dagster-centered MVP: a tenant-scoped export surface over the existing GitHub gold engineering metrics in `kabuto-kurage`.

The export surface should make the current local data platform feel product-facing without cloning Jellyfish's private product or exact API. It should demonstrate the data-platform concerns called out by public Jellyfish research:

- customer-facing data export pipelines;
- engineering metrics exposed outside the orchestration UI;
- tenant-scoped access boundaries;
- API/MCP-shaped interfaces that sit on top of modeled metrics;
- clear documentation of verified public inspiration versus local project assumptions.

## Public Jellyfish Reference Boundary

The local design is inspired only by public facts recorded in `.loom/research/2026-06-18-jellyfish-company-research.md`:

- Jellyfish publicly exposes API/export surfaces used from tools such as Grafana.
- Public examples use token-style authorization and export endpoint paths under `app.jellyfish.co/endpoints/export/v0/...`.
- Public API/MCP categories include metrics, delivery, allocations, people, teams, AI impact, and DevEx.
- Jellyfish's public MCP server wraps its public API and provides AI-agent access to engineering metrics and related data.

This project MUST NOT claim:

- Jellyfish uses the endpoints defined here.
- Jellyfish uses this tenant model, storage model, Delta Lake, Dagster, FastAPI, or this exact MCP design internally.
- These metrics match Jellyfish proprietary metrics.

## Chosen Export Surface

The next milestone should implement a **REST API first**, then add a **minimal MCP wrapper** over the same query/service layer once the REST contract is stable.

Rationale:

- REST is the smallest concrete customer-facing export surface and maps directly to the public Jellyfish API/Grafana evidence.
- A shared query/service layer prevents the MCP wrapper from duplicating metric logic.
- MCP remains relevant because Jellyfish publicly maintains an MCP server, but it should not be the first implementation dependency.

## Existing Metric Inputs

The first export surface is limited to existing gold tables:

| Gold table | Source code | Export use |
| --- | --- | --- |
| `gold/github/pr_throughput_daily` | `PR_THROUGHPUT_DAILY_TABLE` in `src/kabuto_kurage/transforms/github_gold.py` | Daily PR opened/merged/closed counts by tenant, repository, and date. |
| `gold/github/pr_cycle_time` | `PR_CYCLE_TIME_TABLE` in `src/kabuto_kurage/transforms/github_gold.py` | Per-PR open-to-merge cycle time rows. |

The export layer MAY read these Delta tables directly through `deltalake`/`pyarrow` and MAY aggregate them in Python for the local milestone. It MUST NOT depend on raw bronze payloads for the first export milestone.

## REST API Contract

All endpoints use the project convention `/api/v1/...`.

### Authentication and Tenant Scope

Every endpoint MUST require a local API token.

Minimum local auth contract:

- Clients send `Authorization: Bearer <token>`.
- Token values are configured outside git, for example through an ignored local YAML/env file.
- Each token maps to an allowlist of tenant IDs.
- `tenant_id` is always in the path and validated with the existing tenant ID rules.
- Requesting a tenant outside the token allowlist returns `403`.
- Missing/invalid tokens return `401`.
- No endpoint defaults to "all tenants".
- Cross-tenant exports require a future decision and are out of scope for this milestone.

The API MUST never return GitHub token values, raw `payload_json`, local filesystem secrets, or data from a tenant other than the tenant path being requested.

### Endpoint: PR Throughput Daily

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily
```

Maps to:

```text
gold/github/pr_throughput_daily
```

Query parameters:

- `start_date` optional `YYYY-MM-DD`, inclusive filter on `metric_date`.
- `end_date` optional `YYYY-MM-DD`, inclusive filter on `metric_date`.
- `repository_full_name` optional repeatable filter.
- `limit` optional positive integer with a safe default and hard maximum.
- `offset` optional non-negative integer for simple pagination.

Response fields should include:

- `tenant_id`
- `repository_full_name`
- `metric_date`
- `opened_count`
- `merged_count`
- `closed_count`
- `observed_pull_request_count`
- `latest_fetched_at`
- `latest_ingestion_run_id`

### Endpoint: PR Cycle Time Rows

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time
```

Maps to:

```text
gold/github/pr_cycle_time
```

Query parameters:

- `start_date` optional `YYYY-MM-DD`, inclusive filter on `created_at`.
- `end_date` optional `YYYY-MM-DD`, inclusive filter on `created_at`.
- `repository_full_name` optional repeatable filter.
- `merged` optional boolean filter.
- `limit` optional positive integer with a safe default and hard maximum.
- `offset` optional non-negative integer for simple pagination.

Response fields should include:

- `tenant_id`
- `repository_full_name`
- `repository_owner`
- `pull_request_id`
- `pull_request_node_id`
- `number`
- `title`
- `user_login`
- `state`
- `merged`
- `created_at`
- `merged_at`
- `cycle_time_hours`
- `cycle_time_days`
- `fetched_at`
- `ingestion_run_id`

### Endpoint: GitHub Metrics Summary

```text
GET /api/v1/tenants/{tenant_id}/metrics/github/summary
```

Maps to both existing gold tables:

```text
gold/github/pr_throughput_daily
gold/github/pr_cycle_time
```

This endpoint should aggregate a compact portfolio/demo summary from the two metric tables.

Query parameters:

- `start_date` optional `YYYY-MM-DD`.
- `end_date` optional `YYYY-MM-DD`.
- `repository_full_name` optional repeatable filter.

Response fields should include:

- `tenant_id`
- `repositories_observed`
- `opened_count`
- `merged_count`
- `closed_count`
- `pull_requests_observed`
- `merged_pull_requests_observed`
- `median_cycle_time_hours` or `average_cycle_time_hours` (choose one in implementation and document it)
- `latest_fetched_at`

## MCP Follow-Up Contract

After REST endpoints and shared query code exist, add a minimal MCP server that exposes tools corresponding to the same stable export contract.

Initial MCP tools:

| MCP tool | Maps to REST/query contract | Maps to gold metric |
| --- | --- | --- |
| `github_pr_throughput_daily` | `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily` | `gold/github/pr_throughput_daily` |
| `github_pr_cycle_time` | `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time` | `gold/github/pr_cycle_time` |
| `github_metrics_summary` | `GET /api/v1/tenants/{tenant_id}/metrics/github/summary` | both gold tables |

MCP tools MUST require an explicit `tenant_id` argument and MUST enforce the same token/tenant allowlist semantics as REST, either by calling the REST service or by sharing the same auth/query layer.

The MCP server should be documented as a local learning analogue to Jellyfish's public MCP pattern, not as a reproduction of Jellyfish's MCP implementation.

## Acceptance Criteria for the Export Milestone

A future implementation satisfies this spec when:

1. REST endpoints above return tenant-scoped JSON from existing gold Delta tables.
2. Authentication/authorization tests prove missing token, invalid token, allowed tenant, and disallowed tenant behavior.
3. Query filters and pagination are tested with deterministic fixture-backed Delta tables.
4. Responses never include raw bronze payloads or secrets.
5. README/docs include example REST calls and clearly state public Jellyfish inspiration versus project-specific design.
6. The MCP wrapper, if implemented in the same milestone, exposes only the tools listed here and uses the same tenant-scope rules.

## Non-Goals

- Exact compatibility with Jellyfish public API endpoints.
- Reproducing Jellyfish proprietary metrics.
- Multi-tenant admin APIs or cross-tenant benchmarking.
- Production OAuth, SSO, billing, public hosting, or real customer data exposure.
- Exporting raw GitHub payload JSON.
- Building a dashboard before the API contract is stable.

## Related Records

- `.loom/research/2026-06-18-jellyfish-company-research.md`
- `.loom/specs/mini-engineering-intelligence-platform.md`
- `.loom/tickets/2026-06-18-plan-export-api-followup.md`
- `.loom/tickets/2026-06-18-build-gold-engineering-metrics.md`
