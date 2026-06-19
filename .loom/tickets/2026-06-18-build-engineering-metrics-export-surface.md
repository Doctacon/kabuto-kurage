Status: active
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

Active. User approved proceeding with the export/API follow-up milestone on 2026-06-18.

## Journal

- 2026-06-18: Created as follow-up parent plan from `.loom/tickets/2026-06-18-plan-export-api-followup.md`.
- 2026-06-18: Marked blocked because implementing the export surface is a new milestone requiring explicit selection.
- 2026-06-18: User approved proceeding with the follow-up milestone; parent moved to active and query-layer child started.

## Progress and Notes

- 2026-06-18: Created as follow-up parent plan from `.loom/tickets/2026-06-18-plan-export-api-followup.md`.

## Blockers

None for the parent. Child tickets should proceed in dependency order.
