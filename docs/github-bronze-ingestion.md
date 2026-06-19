# GitHub Bronze Ingestion

This milestone adds the first real ingestion path: GitHub REST API data extracted through explicit dlt source/resources into tenant-scoped bronze Delta tables.

## What It Ingests

Initial resources:

- GitHub repositories
- GitHub pull requests

The ingestion uses a dlt source named `github_bronze` with dlt resources named `repositories` and `pull_requests`, plus tenant/source config from `config/tenants.example.yaml` or the path configured by `KABUTO_TENANTS_CONFIG`.

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

Run one tenant through the primary Taskfile workflow:

```bash
task ingest TENANT=sandbox
```

Direct script equivalent:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox
```

Run all configured tenants:

```bash
uv run python tools/ingest_github_bronze.py --all-tenants
```

For safe validation against a temporary data root and limited repository count:

```bash
task ingest TENANT=sandbox DATA_ROOT=/tmp/kabuto-kurage-validation MAX_REPOSITORIES=1
```

Direct script equivalent:

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

## Storage Profile Behavior

The deterministic default profile is `local`, so the physical bronze table paths are
filesystem paths under `.local/data/delta` or `KABUTO_DATA_ROOT/delta`. The storage
profile layer can also resolve equivalent tenant-scoped bronze table URIs for MinIO
and Cloudflare R2 using `KABUTO_STORAGE_PROFILE=minio` or `KABUTO_STORAGE_PROFILE=r2`.

The current ingestion code preserves local filesystem writes for deterministic tests
and portfolio demos. Object-store profiles centralize URI/credential conventions for
Delta and DuckDB engine boundaries; live MinIO/R2 runs require ignored environment
variables and are not required by the test suite.

## dlt Source, Resources, Schema, State, and Rate Limits

GitHub bronze ingestion is represented as an explicit dlt source/resource graph rather than only a hand-written REST loop:

| dlt concept | Project value | Purpose |
| --- | --- | --- |
| Source | `github_bronze` | One tenant-scoped GitHub bronze extraction run. |
| Resource | `repositories` | Configured owner/discovered repositories plus explicit repositories. |
| Resource | `pull_requests` | Pull requests for the final repository set. |
| Write disposition | `replace` | Mirrors the per-tenant/resource overwrite semantics used by the local Delta tables. |
| Primary key hint | `source_id` | Stable GitHub `node_id`, falling back to `id` or URL. |

The resources use dlt's `RESTClient` with `HeaderLinkPaginator` for API extraction. It follows GitHub/RFC 5988-style `Link` headers and continues while a `rel="next"` URL is present.

For each response, ingestion captures these headers when available:

- `x-ratelimit-limit`
- `x-ratelimit-remaining`
- `x-ratelimit-used`
- `x-ratelimit-reset`
- `x-ratelimit-resource`

During resource iteration, ingestion updates dlt source/resource state with tenant ID, ingestion run ID, fetched timestamp, row counts, write disposition, and latest rate-limit snapshot. This gives the project dlt-native schema/state artifacts while the stable bronze Delta envelope remains the downstream contract for silver models. After a run, local dlt inspection artifacts are written under:

```text
.local/data/dlt/github/{tenant_id}/schema.json
.local/data/dlt/github/{tenant_id}/state.json
```

Use these files to inspect the dlt source/resource schema hints and state snapshot without exposing secrets:

```bash
jq '.resource_schemas.repositories' .local/data/dlt/github/sandbox/schema.json
jq '.resources.pull_requests' .local/data/dlt/github/sandbox/state.json
```

`schema.json` includes dlt resource schemas for `repositories` and `pull_requests`, including column hints, `source_id` primary key hints, and `replace` write disposition. `state.json` includes the latest run/resource state and rate-limit snapshots. Neither file stores GitHub token values.

If GitHub returns an HTTP error, ingestion raises `GitHubIngestionError`. If a `403` or `429` response has zero remaining requests, the error message identifies likely rate-limit exhaustion. dlt owns the source/resource and REST extraction/pagination mechanics; the project preserves tenant-scoped Delta bronze tables as the downstream compatibility contract.

## Idempotency Semantics

This first bronze path uses per-tenant/resource **overwrite** writes:

- `repositories` is overwritten for the tenant's configured repository scope.
- `pull_requests` is overwritten for the repositories processed in the run.

That keeps repeated local runs idempotent for the configured scope and avoids duplicate raw rows while preserving raw payloads, run metadata, and dlt schema/state artifacts for the latest extraction. Historical run retention can be introduced later if the project needs immutable append-only bronze history.

## Fixture Mode for Dagster Smoke Tests

Set `KABUTO_GITHUB_FIXTURE_MODE=1` to materialize bronze assets without live GitHub credentials. Fixture mode emits one synthetic repository and one synthetic pull request for the requested tenant, then writes the same bronze schema and dlt schema/state artifacts as the normal path.

Use fixture mode for deterministic local demos and Dagster materialization smoke tests only. It is not live ingestion and should not be used as evidence of GitHub API connectivity.

## Failure Behavior

- Missing token: live ingestion fails before making API requests with a message asking for the configured token env var or `GH_TOKEN`; use `KABUTO_GITHUB_FIXTURE_MODE=1` only for deterministic no-token demos/tests.
- HTTP errors: ingestion fails with the response status and request URL. Rate-limit exhaustion is called out when headers indicate it.
- Unexpected response shape: ingestion fails if list endpoints do not return lists or object endpoints do not return mappings.
- Partial writes: API fetching completes before Delta writes begin, so a fetch failure does not overwrite existing bronze tables.

## Secret Handling

GitHub token values should be stored in Proton Pass or another password manager and
exported into the shell as `GITHUB_TOKEN` or `GH_TOKEN` only when needed. Tenant YAML
stores the env-var name, not the value. Do not commit `.env`, `.local/`, `.dlt/`,
GitHub tokens, MinIO/R2 credentials, or dlt secrets. The dlt schema/state artifacts
record source/resource metadata and row/rate-limit state, not token values.

## Out of Scope

This ticket does not implement silver transforms, Dagster assets, metrics, webhook ingestion, retries, or incremental cursors. Those are tracked by later Loom tickets.
