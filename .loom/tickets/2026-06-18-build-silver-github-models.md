Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md

# Build Silver GitHub Models

## Scope

Transform raw GitHub bronze data into stable silver Delta tables for analytics.

Initial modeled entities:

- Repositories.
- Pull requests.
- Optional: users/authors if needed for metrics.

Expected behavior:

- Preserve tenant identity.
- Extract stable typed columns from raw payloads.
- Keep source IDs and URLs for traceability.
- Handle nulls and missing fields gracefully.
- Document how schema evolution would be handled when GitHub payloads change.

## Out of Scope

- Gold metrics.
- Full dimensional model for every GitHub entity.
- Jira or CI/CD models.

## Acceptance Criteria

- Silver tables are materialized from bronze data.
- Tests cover transformation of representative PR/repository fixtures.
- Silver model documentation includes table columns and intended use.
- A schema-evolution note explains what happens when new GitHub fields appear.

## Current State

Done. Stable silver GitHub repository and pull request models are materialized from tenant-scoped bronze Delta tables.

Implemented:

- `src/kabuto_kurage/transforms/github_silver.py` with typed silver schemas, bronze-to-silver transforms, tenant materialization, and CLI argument parsing.
- `tools/build_github_silver.py` CLI wrapper.
- `tests/test_github_silver_models.py` covering repository/PR fixture transforms, null/missing field handling, silver Delta writes, and tenant path separation.
- `docs/github-silver-models.md` documenting table columns, intended use, missing/null behavior, and schema-evolution handling.
- README and development docs updated with the silver model command and docs link.

Evidence: `.loom/evidence/2026-06-18-github-silver-models.md`.

Review: `.loom/reviews/2026-06-18-github-silver-models-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added GitHub silver transform module, CLI wrapper, tests, docs, and README/development updates.
- 2026-06-18: Ran `uv run pytest`; 23 tests passed.
- 2026-06-18: Ran `uv run ruff check .`; passed.
- 2026-06-18: Ran `uv run mypy src`; passed.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- Silver `repositories` and `pull_requests` tables are materialized from bronze Delta data via `materialize_tenant_github_silver()`.
- Tenant identity is preserved in each silver record and tenant-scoped silver Delta paths remain separate.
- Source IDs and URLs are preserved through payload IDs/URLs and `bronze_source_id`, `bronze_source_url`, and `bronze_api_url` columns.
- Typed stable columns are extracted for repository inventory and pull-request analytics.
- Missing/null fields are handled gracefully by nullable typed columns and safe extraction helpers.
- Tests cover representative PR/repository fixtures and bronze-to-silver Delta materialization.
- `docs/github-silver-models.md` includes table columns, intended use, missing/null behavior, and schema-evolution notes.

## Blockers

None for this ticket. Downstream tickets remain responsible for Dagster asset graph integration, gold metrics, tenant isolation validation beyond path separation, and observability/freshness.
