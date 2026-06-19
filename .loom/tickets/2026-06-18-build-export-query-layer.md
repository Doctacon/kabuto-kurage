Status: blocked
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md
Depends-On: .loom/specs/engineering-metrics-export-surface.md, .loom/tickets/2026-06-18-build-gold-engineering-metrics.md

# Build Export Query Layer

## Scope

Implement shared query functions over the existing gold GitHub Delta metric tables. This layer should be usable by both the future REST API and MCP wrapper.

Expected query functions:

- Read `gold/github/pr_throughput_daily` for a tenant with date/repository filters, limit, and offset.
- Read `gold/github/pr_cycle_time` for a tenant with date/repository/merged filters, limit, and offset.
- Produce a compact GitHub metrics summary from both gold tables.

## Out of Scope

- HTTP routes.
- MCP server/tools.
- Dashboard UI.
- Reading raw bronze payloads.

## Acceptance Criteria

- Query functions read only tenant-scoped gold Delta paths for the requested tenant.
- Query functions validate `tenant_id` and fail clearly when tables are missing.
- Filters and pagination are covered by deterministic fixture-backed tests.
- Returned records are JSON-serializable or have a clearly tested serialization helper.
- No raw `payload_json`, token values, or cross-tenant data are returned.

## Progress and Notes

- Not started.

## Current State

Blocked pending operator/product decision to begin the export/API follow-up milestone.

## Journal

- 2026-06-18: Created as the first executable child of the export/API follow-up plan.
- 2026-06-18: Marked blocked until the follow-up milestone is explicitly selected for execution.

## Blockers

- Requires implementation approval for the export/API follow-up milestone.
