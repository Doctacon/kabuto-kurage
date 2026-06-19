Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md

# Migrate Bronze to dlt-Native GitHub Source

## Scope

Move GitHub bronze ingestion from a mostly project-shaped raw envelope to a more dlt-native source/resource/schema/state implementation.

Expected behavior:

- Define explicit dlt GitHub source/resources for repositories and pull requests.
- Let dlt own more schema/resource/state behavior.
- Preserve tenant identity in persisted records or tenant-scoped paths.
- Preserve raw payload auditability or document the replacement dlt-normalized/raw-source artifact.
- Keep silver models as the compatibility boundary between source layout and analytics models.
- Keep pagination, rate-limit handling, idempotency/incrementality, and token safety testable.

## Out of Scope

- Adding new GitHub resource types beyond repositories and pull requests unless needed for dlt design.
- Changing gold metric semantics.
- Requiring live GitHub credentials in deterministic tests.
- Rewriting REST/MCP contracts.

## Acceptance Criteria

- GitHub ingestion uses dlt source/resource/schema/state concepts directly.
- Tests prove tenant isolation, pagination, rate-limit metadata or equivalent observability, no token leakage, and repeat-run behavior.
- Silver model tests pass or are intentionally adapted to the new bronze layout.
- Docs explain dlt schema/state artifacts and how to inspect them.
- Full downstream test/lint/typecheck validation passes.

## Current State

Done. GitHub bronze ingestion now uses explicit dlt source/resource/schema/state concepts while preserving the existing tenant-scoped Delta bronze and downstream silver/gold/Dagster/REST/MCP contracts.

Evidence: `.loom/evidence/2026-06-19-dlt-native-github-bronze-source-validation.md`.

Review: `.loom/reviews/2026-06-19-dlt-native-github-bronze-source-review.md`.

## Journal

- 2026-06-19: Set active and delegated dlt-native GitHub bronze migration to worker.
- 2026-06-19: Added dlt source `github_bronze` with dlt resources `repositories` and `pull_requests`.
- 2026-06-19: Added dlt resource schema hints, source/resource state updates, and local schema/state inspection artifacts.
- 2026-06-19: Preserved raw `payload_json`, tenant-scoped Delta bronze paths, overwrite behavior, rate-limit metadata, and downstream silver compatibility.
- 2026-06-19: Updated ingestion/Dagster tests and docs.
- 2026-06-19: Validated with focused ingestion/silver/isolation tests and full `pytest`/`ruff`/`mypy` suite.
- 2026-06-19: Recorded evidence/review and moved ticket to done.

## Progress and Notes

- 2026-06-19: Implemented dlt-native source/resource construction in `src/kabuto_kurage/ingestion/github_bronze.py`.
- 2026-06-19: Added `schema.json` and `state.json` local dlt inspection artifacts under `.local/data/dlt/github/{tenant_id}/`.
- 2026-06-19: Updated `tests/test_github_bronze_ingestion.py` to prove dlt resource shape, artifact contents, pagination, rate-limit capture, no token leakage, and repeat-run behavior.
- 2026-06-19: Updated `tests/test_dagster_assets.py` for the enriched ingestion result object.
- 2026-06-19: Updated `docs/github-bronze-ingestion.md` with dlt source/resource/schema/state inspection guidance.

## Results

Acceptance criteria satisfied:

- GitHub ingestion uses dlt source/resource/schema/state concepts directly.
- Tests prove tenant isolation, pagination, rate-limit metadata, no token leakage, and repeat-run behavior.
- Silver model tests pass unchanged.
- Docs explain dlt schema/state artifacts and how to inspect them.
- Full downstream test/lint/typecheck validation passes.

## Blockers

None.
