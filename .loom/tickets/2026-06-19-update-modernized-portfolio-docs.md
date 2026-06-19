Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-migrate-bronze-to-dlt-native-github-source.md, .loom/tickets/2026-06-19-query-gold-metrics-with-duckdb.md, .loom/tickets/2026-06-19-add-taskfile-developer-workflow.md

# Update Modernized Portfolio Docs

## Scope

Update portfolio-facing documentation after the modernized storage/ingestion/query/dev-workflow implementation lands.

Expected docs updates:

- README architecture narrative.
- `docs/architecture.md` diagrams and walkthrough.
- `docs/github-bronze-ingestion.md` for dlt-native source/resources/schema/state.
- `docs/stack-validation.md` for DuckDB/dlt/object-storage validation.
- `docs/export-api.md` for DuckDB-backed query layer if relevant.
- `docs/local-iac.md` for MinIO/storage profiles if relevant.
- Developer workflow docs for Taskfile.
- Secret handling guidance for Proton Pass/env vars.

## Out of Scope

- Implementing storage/query/ingestion code changes.
- Publishing public docs.
- Adding a dashboard.

## Acceptance Criteria

- Docs accurately reflect implemented storage profiles, dlt-native ingestion, DuckDB query layer, and Taskfile commands.
- Docs preserve public-Jellyfish inspiration boundaries and do not claim internals.
- Docs do not include real secrets, bucket names, account IDs, or tokens.
- Documentation tests are updated or added where appropriate.
- Full test/lint/typecheck validation passes.

## Current State

Done. Portfolio-facing documentation now reflects the modernized storage profiles, dlt-native bronze ingestion, DuckDB query layer, Taskfile workflow, and safe Proton Pass/env-var secret handling.

Evidence: `.loom/evidence/2026-06-19-modernized-portfolio-docs-validation.md`.

Review: `.loom/reviews/2026-06-19-modernized-portfolio-docs-review.md`.

## Journal

- 2026-06-19: Set active and delegated final modernized docs update to worker.
- 2026-06-19: Updated README, architecture, bronze ingestion, stack validation, export API, local IaC, and development docs for storage profiles, dlt source/resources, DuckDB, Taskfile, and Proton Pass/env-var secret handling.
- 2026-06-19: Added `tests/test_modernized_portfolio_docs.py` and updated `tests/test_portfolio_docs.py` for the new dlt source/resources wording.
- 2026-06-19: Validated with `uv run pytest tests/test_modernized_portfolio_docs.py -q`, `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- 2026-06-19: Recorded evidence and review; moved ticket to done.

## Progress and Notes

- 2026-06-19: Updated portfolio docs after implementation tickets landed.
- 2026-06-19: Validation passed: `84 passed`, Ruff passed, mypy passed.

## Results

Acceptance criteria satisfied:

- Docs accurately reflect implemented storage profiles, dlt-native ingestion, DuckDB query layer, and Taskfile commands.
- Docs preserve public-Jellyfish inspiration boundaries and do not claim internals.
- Docs do not include real secrets, bucket names, account IDs, or tokens.
- Documentation tests were added/updated.
- Full test/lint/typecheck validation passes.

## Blockers

None.
