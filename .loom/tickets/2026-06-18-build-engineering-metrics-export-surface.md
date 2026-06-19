Status: blocked
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/specs/engineering-metrics-export-surface.md, .loom/tickets/2026-06-18-build-gold-engineering-metrics.md

# Build Engineering Metrics Export Surface

## Scope

Parent follow-up plan for implementing the export/API milestone shaped by `.loom/specs/engineering-metrics-export-surface.md`.

This is not the current implementation ticket. It coordinates future executable child tickets that should expose existing gold GitHub metrics through a tenant-scoped REST API first, then optionally through a minimal MCP wrapper over the same query/service layer.

## Chosen Surface

- Primary surface: REST API under `/api/v1`.
- Secondary surface: minimal MCP wrapper after REST and shared query/auth logic are stable.
- Metric inputs: existing gold Delta tables only:
  - `gold/github/pr_throughput_daily`;
  - `gold/github/pr_cycle_time`.

## Child Tickets

1. `.loom/tickets/2026-06-18-build-export-query-layer.md`
   - Create shared read/query functions over gold Delta tables.
   - No HTTP/MCP yet.

2. `.loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md`
   - Add REST API endpoints and tenant-scoped token authorization.

3. `.loom/tickets/2026-06-18-document-and-validate-export-api.md`
   - Add docs, examples, and validation for the REST export surface.

4. `.loom/tickets/2026-06-18-add-minimal-mcp-wrapper.md`
   - Add a minimal MCP wrapper over the stable export query/API contract.

## Sequencing

Recommended sequence:

1. Query layer first.
2. REST API second.
3. Documentation/validation third.
4. MCP wrapper last; defer if REST contract or tenant auth needs more iteration.

## Acceptance Criteria

The parent follow-up can close when:

- REST endpoints from `.loom/specs/engineering-metrics-export-surface.md` return tenant-scoped JSON from existing gold Delta tables.
- Tenant-scoped token auth has tests for missing, invalid, allowed, and disallowed tenant behavior.
- API docs include examples and public-Jellyfish-inspiration disclaimers.
- MCP wrapper is either implemented against the same query/auth layer or explicitly split into a later parent ticket.

## Current State

Blocked pending an operator/product decision to start the export/API follow-up milestone. The Dagster-centered MVP parent does not require implementing this follow-up.

## Journal

- 2026-06-18: Created as follow-up parent plan from `.loom/tickets/2026-06-18-plan-export-api-followup.md`.
- 2026-06-18: Marked blocked because implementing the export surface is a new milestone requiring explicit selection.

## Progress and Notes

- 2026-06-18: Created as follow-up parent plan from `.loom/tickets/2026-06-18-plan-export-api-followup.md`.

## Blockers

- Awaiting operator/product decision to execute the export/API follow-up milestone.
