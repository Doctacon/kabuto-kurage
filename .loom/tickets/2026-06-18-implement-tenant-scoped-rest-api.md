Status: blocked
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md
Depends-On: .loom/tickets/2026-06-18-build-export-query-layer.md, .loom/specs/engineering-metrics-export-surface.md

# Implement Tenant-Scoped REST API

## Scope

Expose the export query layer through a local REST API under `/api/v1`.

Required endpoints from `.loom/specs/engineering-metrics-export-surface.md`:

- `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily`
- `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time`
- `GET /api/v1/tenants/{tenant_id}/metrics/github/summary`

Required tenant access behavior:

- Require `Authorization: Bearer <token>`.
- Map tokens to explicit tenant allowlists through ignored local config or environment-derived settings.
- Return `401` for missing/invalid tokens.
- Return `403` when a valid token asks for a tenant outside its allowlist.
- Never default to all tenants.

## Out of Scope

- MCP wrapper.
- Dashboard UI.
- Production OAuth/SSO.
- Exact compatibility with Jellyfish public API paths.

## Acceptance Criteria

- API server can be run locally with documented command.
- All three endpoints return JSON from existing gold metric query functions.
- Auth/tenant access behavior is tested for missing token, invalid token, allowed tenant, and disallowed tenant.
- Endpoint tests prove tenant A cannot read tenant B data.
- Response schemas and error responses are documented.

## Progress and Notes

- Not started.

## Current State

Blocked. This belongs to the export/API follow-up milestone, which is awaiting explicit operator/product selection, and it also depends on the query layer ticket.

## Journal

- 2026-06-18: Created as a future child of the export/API follow-up plan.
- 2026-06-18: Marked blocked pending export/API milestone selection and query-layer completion.

## Blockers

- Requires query layer ticket.
- Requires operator/product decision to begin the export/API follow-up milestone.
