# GitHub Silver Models

This milestone transforms tenant-scoped GitHub bronze Delta tables into stable silver Delta models for downstream analytics.

Silver models are intentionally narrower than raw bronze payloads:

- Bronze keeps canonical `payload_json` for source fidelity and schema-evolution inspection.
- Silver extracts typed, stable columns that are useful for analytics and later gold metrics.
- Silver preserves tenant identity and source traceability so downstream code does not need to reopen raw payloads for common fields.

## Running Locally

Run bronze ingestion first:

```bash
uv run python tools/ingest_github_bronze.py --tenant sandbox --max-repositories 1
```

Then build silver tables for one tenant:

```bash
uv run python tools/build_github_silver.py --tenant sandbox
```

Or build all configured tenants:

```bash
uv run python tools/build_github_silver.py --all-tenants
```

For validation against a temporary data root, pass the same `--data-root` to both commands:

```bash
uv run python tools/ingest_github_bronze.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation \
  --max-repositories 1

uv run python tools/build_github_silver.py \
  --tenant sandbox \
  --data-root /tmp/kabuto-kurage-validation
```

## Storage Layout

Silver tables follow the same tenant-scoped path convention as bronze:

```text
.local/data/delta/tenants/{tenant_id}/silver/github/repositories
.local/data/delta/tenants/{tenant_id}/silver/github/pull_requests
```

Writes use overwrite semantics for this first local snapshot-style model. Re-running the transform replaces the tenant's silver snapshot with the latest bronze-derived records.

## `silver/github/repositories`

Intended use: stable repository dimension-like data for later metrics, repository filtering, and tenant-scoped inventory checks.

| Column | Type | Meaning |
| --- | --- | --- |
| `tenant_id` | string | Logical tenant ID from the bronze row. |
| `source` | string | Source system, currently `github`. |
| `repository_id` | int64 | GitHub repository numeric ID. |
| `repository_node_id` | string | GitHub GraphQL/global node ID. |
| `owner_login` | string | Repository owner login. |
| `name` | string | Repository short name. |
| `full_name` | string | GitHub `owner/name`. |
| `private` | boolean | Whether GitHub marks the repository private. |
| `fork` | boolean | Whether the repository is a fork. |
| `archived` | boolean | Whether the repository is archived. |
| `disabled` | boolean | Whether the repository is disabled. |
| `default_branch` | string | Default branch name. |
| `language` | string | Primary language reported by GitHub. |
| `description` | string | Repository description. |
| `html_url` | string | Browser URL. |
| `api_url` | string | GitHub API URL. |
| `created_at` | timestamp UTC | Repository creation time. |
| `updated_at` | timestamp UTC | Repository update time. |
| `pushed_at` | timestamp UTC | Last push time. |
| `fetched_at` | timestamp UTC | Bronze ingestion fetch timestamp. |
| `ingestion_run_id` | string | Bronze ingestion run ID. |
| `bronze_source_id` | string | Bronze `source_id`, preserved for traceability. |
| `bronze_source_url` | string | Bronze `source_url`, preserved for traceability. |
| `bronze_api_url` | string | Bronze `api_url`, preserved for traceability. |

## `silver/github/pull_requests`

Intended use: stable pull-request fact-like data for later PR throughput, cycle time, merge latency, and review-related metrics.

| Column | Type | Meaning |
| --- | --- | --- |
| `tenant_id` | string | Logical tenant ID from the bronze row. |
| `source` | string | Source system, currently `github`. |
| `pull_request_id` | int64 | GitHub pull request numeric ID. |
| `pull_request_node_id` | string | GitHub GraphQL/global node ID. |
| `repository_full_name` | string | Base repository `owner/name`, falling back to bronze `source_repo`. |
| `repository_owner` | string | Owner parsed from `repository_full_name`. |
| `number` | int64 | Pull request number within the repository. |
| `state` | string | GitHub PR state, such as `open` or `closed`. |
| `title` | string | Pull request title. |
| `user_login` | string | PR author login when present. |
| `author_association` | string | GitHub author association. |
| `draft` | boolean | Whether the PR is a draft when present in payload. |
| `merged` | boolean | Derived as `merged_at is not null`. |
| `created_at` | timestamp UTC | PR creation time. |
| `updated_at` | timestamp UTC | PR update time. |
| `closed_at` | timestamp UTC | PR close time. |
| `merged_at` | timestamp UTC | PR merge time. |
| `html_url` | string | Browser URL. |
| `api_url` | string | GitHub API URL. |
| `base_ref` | string | Base branch ref. |
| `head_ref` | string | Head branch ref. |
| `base_repo_full_name` | string | Base repo `owner/name`. |
| `head_repo_full_name` | string | Head repo `owner/name`, which may differ for forks. |
| `fetched_at` | timestamp UTC | Bronze ingestion fetch timestamp. |
| `ingestion_run_id` | string | Bronze ingestion run ID. |
| `bronze_source_id` | string | Bronze `source_id`, preserved for traceability. |
| `bronze_source_url` | string | Bronze `source_url`, preserved for traceability. |
| `bronze_api_url` | string | Bronze `api_url`, preserved for traceability. |

## Missing and Null Fields

GitHub payloads vary by endpoint, permissions, repository state, and API evolution. The silver transform handles missing or null fields by writing nulls for nullable typed columns rather than failing. Examples:

- Missing `owner.login` writes null `owner_login` unless bronze `source_owner` can provide a fallback.
- Missing `user.login` writes null `user_login`.
- Missing nested repo objects write null branch/repo columns while preserving bronze source URLs and IDs.
- Invalid or absent timestamps write null timestamp values.

Invalid JSON in `payload_json` fails the transform because the bronze row is unreadable and should be corrected or regenerated.

## Schema Evolution Note

New GitHub fields should first land safely in bronze `payload_json`; no silver schema change is required just because GitHub adds data. A field should be promoted to silver only when downstream analytics need it as a stable contract.

When promoting a new field:

1. Add a nullable typed column to the relevant silver schema.
2. Extract it with a helper that tolerates missing, null, or differently typed values.
3. Add fixture-based tests covering old payloads without the field and new payloads with the field.
4. Document the new column here.
5. Backfill silver from bronze; historical bronze payloads that lack the field will produce nulls.

Breaking source changes should be handled by updating extraction logic while preserving the silver contract where possible. If a true semantic change cannot be represented in the existing table, prefer adding a new nullable column or compatibility view over silently changing column meaning.

## Out of Scope

This silver milestone does not compute gold metrics, build Dagster assets, add webhook/event ingestion, or model every GitHub entity. Those are tracked by later Loom tickets.
