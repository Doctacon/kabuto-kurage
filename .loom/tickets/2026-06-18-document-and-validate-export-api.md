Status: blocked
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

- Not started.

## Current State

Blocked. This belongs to the export/API follow-up milestone, which is awaiting explicit operator/product selection, and it also depends on REST API implementation.

## Journal

- 2026-06-18: Created as a future child of the export/API follow-up plan.
- 2026-06-18: Marked blocked pending export/API milestone selection and REST API implementation.

## Blockers

- Requires REST API implementation.
- Requires operator/product decision to begin the export/API follow-up milestone.
