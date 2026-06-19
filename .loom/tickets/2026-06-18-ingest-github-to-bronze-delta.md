Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-model-tenants-and-source-config.md

# Ingest GitHub to Bronze Delta

## Scope

Build the first real ingestion path from GitHub API to raw/bronze Delta Lake tables.

Initial resources:

- Repositories.
- Pull requests.

Expected behavior:

- Authenticate with GitHub token from environment/local secret.
- Handle pagination.
- Capture basic rate-limit information when available.
- Persist raw API payloads with metadata: `tenant_id`, source, resource type, fetched timestamp, source identifiers, and ingestion run ID.
- Make repeated runs idempotent or document duplicate-handling limitations.

## Out of Scope

- Complex transformations.
- Full webhook/event ingestion.
- All GitHub resource types.

## Acceptance Criteria

- A configured tenant can ingest GitHub repositories and pull requests into bronze Delta tables.
- Raw records preserve the original payload or enough source JSON for schema-evolution learning.
- Basic tests cover payload normalization into bronze records using fixtures.
- Execution notes document API limits and failure behavior.

## Current State

Done. GitHub REST API ingestion now writes configured tenant repositories and pull requests into tenant-scoped bronze Delta tables.

Implemented:

- `src/kabuto_kurage/ingestion/github_bronze.py` with:
  - explicit GitHub REST client using `httpx`;
  - `Link` header pagination;
  - `x-ratelimit-*` header capture;
  - repository and pull-request fetch helpers;
  - raw payload to bronze record normalization;
  - per-tenant/resource Delta overwrite writes;
  - CLI argument parsing.
- `tools/ingest_github_bronze.py` CLI wrapper.
- `tests/test_github_bronze_ingestion.py` with deterministic mocked HTTP tests covering normalization, pagination, rate-limit capture, Delta writes, and overwrite idempotency.
- `docs/github-bronze-ingestion.md` with execution notes, API limits, failure behavior, bronze columns, pagination, rate-limit capture, and idempotency semantics.
- README and development docs updated with ingestion commands.

Evidence: `.loom/evidence/2026-06-18-github-bronze-ingestion.md`.

Review: `.loom/reviews/2026-06-18-github-bronze-ingestion-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added GitHub bronze ingestion module, CLI wrapper, docs, tests, and README/development updates.
- 2026-06-18: Ran `uv run pytest`; 18 tests passed.
- 2026-06-18: Ran `uv run ruff check .`; passed.
- 2026-06-18: Ran `uv run mypy src`; passed.
- 2026-06-18: Ran live validation using `gh auth token` without printing or committing the token. Temporary config for `octocat/Hello-World` ingested 1 repository row and 1,646 pull request rows into a temporary data root.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- A configured tenant can ingest GitHub repositories and pull requests into bronze Delta tables. This is covered by deterministic tests and live validation.
- Raw records preserve canonical original payload JSON in `payload_json` for schema-evolution learning.
- Bronze metadata includes `tenant_id`, `source`, `resource_type`, `fetched_at`, `source_id`, `source_owner`, `source_repo`, `source_url`, `api_url`, `ingestion_run_id`, and `rate_limit_json`.
- Pagination is handled through GitHub `Link` headers and tested with mocked multi-page responses.
- Rate-limit information is captured from `x-ratelimit-*` headers and stored as JSON.
- Tests cover payload normalization into bronze records using fixture-like mocked payloads.
- Execution notes document API limits and failure behavior in `docs/github-bronze-ingestion.md`.

## Blockers

None for this ticket. Downstream tickets remain responsible for silver models, Dagster asset graph integration, metrics, retries, incremental cursors, and webhook/event ingestion.
