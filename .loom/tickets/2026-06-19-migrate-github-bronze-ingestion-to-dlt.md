Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/decisions/use-dlt-for-github-ingestion.md, .loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md

# Migrate GitHub Bronze Ingestion to dlt

## Scope

Make `dlt` / dlthub the required ingestion/extraction layer for GitHub bronze ingestion while preserving the existing tenant-scoped Delta bronze schema and downstream silver/gold/Dagster/API/MCP contracts.

In scope:

- Add `dlt` as a first-class runtime dependency if not already present.
- Refactor `src/kabuto_kurage/ingestion/github_bronze.py` so GitHub API extraction uses dlt REST helpers/pagination instead of a hand-rolled direct HTTP client loop.
- Keep bronze records, Delta table paths, overwrite semantics, rate-limit metadata, and result objects compatible with the current downstream pipeline.
- Update tests to prove dlt is used for GitHub API extraction and the existing bronze behavior still holds.
- Update README/docs/stack validation/architecture docs so they describe dlt as the ingestion layer.
- Record evidence/review for validation.

## Out of Scope

- Rewriting silver/gold models.
- Changing Delta table layout or schemas.
- Changing Dagster asset names or export API/MCP contracts.
- Moving all storage writes into dlt destinations unless required for the migration.
- Adding new sources beyond GitHub.

## Acceptance Criteria

- GitHub bronze ingestion uses dlt REST/pagination primitives for API extraction.
- Existing deterministic ingestion tests still prove pagination, rate-limit capture, idempotent Delta writes, raw payload retention, and no token leakage.
- README and docs identify dlt as the ingestion layer.
- Downstream tests for silver, gold, Dagster, REST API, and MCP still pass without contract changes.
- `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` pass.

## Progress and Notes

- 2026-06-19: User clarified dlt is mandatory for ingestion.
- 2026-06-19: Created decision `.loom/decisions/use-dlt-for-github-ingestion.md` and this migration ticket.
- 2026-06-19: Added `dlt>=1.28.0` as a runtime dependency.
- 2026-06-19: Refactored `GitHubRestClient` to use dlt `RESTClient`, `BearerTokenAuth`, and `HeaderLinkPaginator` for GitHub extraction/pagination.
- 2026-06-19: Preserved existing bronze Delta schema, tenant-scoped table paths, overwrite semantics, rate-limit metadata, result object shape, and CLI behavior.
- 2026-06-19: Updated deterministic ingestion tests to drive dlt through a local `requests` adapter and prove pagination, rate-limit capture, raw payload retention, idempotent writes, and no token leakage.
- 2026-06-19: Updated README, architecture, bronze ingestion, stack validation docs, and stack validation script to identify dlt as the GitHub ingestion layer.
- 2026-06-19: Validated with `uv run pytest`, `uv run ruff check .`, `uv run mypy src`, and `uv run python tools/validate_stack.py`.

## Current State

Done. GitHub bronze ingestion now uses dlt REST extraction/pagination primitives while preserving downstream contracts.

Evidence: `.loom/evidence/2026-06-19-dlt-github-bronze-ingestion-validation.md`.

Review: `.loom/reviews/2026-06-19-dlt-github-bronze-ingestion-review.md`.

## Results

Acceptance criteria satisfied:

- GitHub bronze ingestion uses dlt REST/pagination primitives for API extraction.
- Deterministic ingestion tests prove pagination, rate-limit capture, idempotent Delta writes, raw payload retention, and no token leakage.
- README and docs identify dlt as the ingestion layer.
- Downstream silver, gold, Dagster, REST API, and MCP tests pass without contract changes.
- `uv run pytest`, `uv run ruff check .`, and `uv run mypy src` pass.

## Blockers

None.
