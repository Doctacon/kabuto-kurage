Status: done
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

- 2026-06-18: Added FastAPI/uvicorn dependencies for an open-source local REST API surface.
- 2026-06-18: Added importable API app at `kabuto_kurage.api.app:app` with `create_app()`.
- 2026-06-18: Added tenant-scoped bearer-token auth with explicit token-to-tenant allowlists from `KABUTO_API_TOKENS_JSON` or `KABUTO_API_TOKENS_CONFIG` using `token_env` references.
- 2026-06-18: Added required `/api/v1/tenants/{tenant_id}/metrics/github/...` endpoints over the shared query layer.
- 2026-06-18: Added endpoint docs in `docs/export-api.md`.
- 2026-06-18: Added deterministic endpoint tests in `tests/test_export_rest_api.py`.
- 2026-06-18: Validated with `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Current State

Done. The local tenant-scoped REST API is implemented and validated.

Evidence: `.loom/evidence/2026-06-18-tenant-scoped-rest-api-validation.md`.

Review: `.loom/reviews/2026-06-18-tenant-scoped-rest-api-review.md`.

## Journal

- 2026-06-18: Created as a future child of the export/API follow-up plan.
- 2026-06-18: Marked blocked pending export/API milestone selection and query-layer completion.
- 2026-06-18: Query layer completed; moved to active and delegated REST API implementation to worker.
- 2026-06-18: Implemented FastAPI app, auth config loader, endpoint tests, and API docs.
- 2026-06-18: Recorded validation evidence and review.
- 2026-06-18: Moved ticket to done after validation passed.

## Blockers

None.
