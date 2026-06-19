Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md
Depends-On: .loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md

# Document and Validate Export API

## Scope

Make the REST export surface understandable as a portfolio artifact and validate it end-to-end against deterministic local data.

Expected docs:

- API overview and run command.
- Example `curl` calls for each endpoint.
- Response examples for throughput, cycle time, summary, and auth errors.
- Tenant-scoped access explanation.
- Public Jellyfish API/MCP inspiration boundary.

Expected validation:

- Tests or evidence for endpoint responses from fixture-backed gold tables.
- Tests or evidence for auth and tenant isolation.
- README/docs map export endpoints to gold metrics.

## Out of Scope

- Implementing new endpoints beyond the spec.
- MCP wrapper implementation.
- Public deployment.

## Acceptance Criteria

- README or docs include accurate endpoint examples and setup steps.
- Documentation states that the API is Jellyfish-inspired by public export/API evidence but not API-compatible with Jellyfish.
- Validation evidence records commands and outputs.
- Existing test/lint/typecheck suite passes after docs/API work.

## Progress and Notes

- 2026-06-18: Expanded `docs/export-api.md` with setup, token config, endpoint-to-gold mapping, curl examples, response/error examples, tenant-scoped access rules, and public Jellyfish boundary.
- 2026-06-18: Updated `README.md` and `docs/architecture.md` so the REST export API is represented as an implemented portfolio surface.
- 2026-06-18: Added `tests/test_export_api_docs.py` and updated `tests/test_portfolio_docs.py` to keep export API documentation claims covered by deterministic tests.
- 2026-06-18: Validated with `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Current State

Done. REST export API portfolio docs and validation evidence satisfy the ticket acceptance criteria.

## Journal

- 2026-06-18: Created as a future child of the export/API follow-up plan.
- 2026-06-18: Marked blocked pending export/API milestone selection and REST API implementation.
- 2026-06-18: REST API implementation completed; moved to active and delegated docs/validation to worker.
- 2026-06-18: Completed docs and validation pass. Evidence recorded in `.loom/evidence/2026-06-18-export-api-docs-validation.md`; review recorded in `.loom/reviews/2026-06-18-export-api-docs-review.md`.
- 2026-06-18: Moved ticket to done.

## Results

Acceptance criteria satisfied:

- README/docs include accurate endpoint examples and setup steps.
- Documentation states that the API is inspired by public Jellyfish API/export evidence but is not API-compatible with Jellyfish.
- Documentation maps each endpoint to existing gold metric tables.
- Tenant-scoped access expectations and auth error behavior are explicit.
- Validation evidence records commands and outputs.
- Existing test/lint/typecheck suite passes.
- No endpoints beyond the spec and no MCP code were added.

## Blockers

None.
