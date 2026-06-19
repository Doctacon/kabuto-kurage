# GitHub Bronze Ingestion

This milestone adds the first real ingestion path: GitHub REST API data into tenant-scoped bronze Delta tables.

## What It Ingests

Initial resources:

- GitHub repositories
- GitHub pull requests

The ingestion uses tenant/source config from `config/tenants.example.yaml` or the path configured by `KABUTO_TENANTS_CONFIG`.

For each tenant, the GitHub source can specify:

- `owners`: GitHub account names whose public repositories should be discovered via `/users/{owner}/repos`
- `repositories`: explicit `owner/name` repositories fetched via `/repos/{owner}/{repo}`

Discovered and explicit repositories are deduplicated by `full_name`. Pull requests are fetched for each final repository with `state=all`.

## Running Locally

Set a GitHub token in your shell or ignored `.env` file. The token value must never be committed.

```bash
export GITHUB_TOKEN=...
# or export GH_TOKEN=...
```

Optionally copy and edit tenant config:

```bash
cp config/tenants.example.yaml config/tenants.local.yaml
export KABUTO_TENANTS_CONFIG=config/tenants.local.yaml
```

Run one tenant:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox
```

Run all configured tenants:

```bash
uv run python tools/ingest_github_bronze.py --all-tenants
```

For safe validation against a temporary data root and limited repository count:

```bash
uv run python tools/ingest_github_bronze.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation \
  --max-repositories 1
```

## Bronze Table Layout

Tables are written under the tenant-scoped Delta convention from `docs/tenancy.md`:

```text
.local/data/delta/tenants/{tenant_id}/bronze/github/repositories
.local/data/delta/tenants/{tenant_id}/bronze/github/pull_requests
```

Each row includes:

| Column | Meaning |
| --- | --- |
| `tenant_id` | Logical tenant ID from config. |
| `source` | Always `github` for this ingestion path. |
| `resource_type` | `repositories` or `pull_requests`. |
| `fetched_at` | UTC timestamp for the ingestion run. |
| `source_id` | GitHub `node_id`, falling back to `id` or `url`. |
| `source_owner` | GitHub owner/login when available. |
| `source_repo` | Repository full name when available. |
| `source_url` | Browser URL from the GitHub payload. |
| `api_url` | API URL from the GitHub payload. |
| `ingestion_run_id` | UUID or caller-provided ID for the run. |
| `payload_json` | Canonical JSON copy of the original API payload. |
| `rate_limit_json` | Rate-limit headers captured from GitHub responses when available. |

`payload_json` is intentionally retained so later schema-evolution exercises can inspect raw source fields that are not yet modeled in silver tables.

## Pagination and Rate Limits

The GitHub client follows RFC 5988-style `Link` headers and continues while a `rel="next"` URL is present.

For each response, ingestion captures these headers when available:

- `x-ratelimit-limit`
- `x-ratelimit-remaining`
- `x-ratelimit-used`
- `x-ratelimit-reset`
- `x-ratelimit-resource`

If GitHub returns an HTTP error, ingestion raises `GitHubIngestionError`. If a `403` or `429` response has zero remaining requests, the error message identifies likely rate-limit exhaustion.

## Idempotency Semantics

This first bronze path uses per-tenant/resource **overwrite** writes:

- `repositories` is overwritten for the tenant's configured repository scope.
- `pull_requests` is overwritten for the repositories processed in the run.

That keeps repeated local runs idempotent for the configured scope and avoids duplicate raw rows while preserving raw payloads and run metadata in the latest table snapshot. Historical run retention can be introduced later if the project needs immutable append-only bronze history.

## Failure Behavior

- Missing token: ingestion fails before making API requests with a message asking for the configured token env var or `GH_TOKEN`.
- HTTP errors: ingestion fails with the response status and request URL. Rate-limit exhaustion is called out when headers indicate it.
- Unexpected response shape: ingestion fails if list endpoints do not return lists or object endpoints do not return mappings.
- Partial writes: API fetching completes before Delta writes begin, so a fetch failure does not overwrite existing bronze tables.

## Out of Scope

This ticket does not implement silver transforms, Dagster assets, metrics, webhook ingestion, retries, or incremental cursors. Those are tracked by later Loom tickets.
