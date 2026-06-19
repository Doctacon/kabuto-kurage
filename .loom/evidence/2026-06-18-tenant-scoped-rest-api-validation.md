Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md, .loom/specs/engineering-metrics-export-surface.md

# Tenant-Scoped REST API Validation

## What Was Observed

Implemented and validated a local FastAPI REST app over the shared GitHub metrics query layer.

Changed files observed in the working tree:

```text
.loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md
pyproject.toml
uv.lock
docs/export-api.md
src/kabuto_kurage/api/__init__.py
src/kabuto_kurage/api/app.py
src/kabuto_kurage/api/auth.py
tests/test_export_rest_api.py
.loom/evidence/2026-06-18-tenant-scoped-rest-api-validation.md
.loom/reviews/2026-06-18-tenant-scoped-rest-api-review.md
```

Primary behavior added:

- Importable app at `kabuto_kurage.api.app:app` with `create_app()` factory.
- Local run command documented as `uv run uvicorn kabuto_kurage.api.app:app --reload`.
- REST endpoints:
  - `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily`
  - `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time`
  - `GET /api/v1/tenants/{tenant_id}/metrics/github/summary`
- Bearer token auth via `Authorization: Bearer <token>`.
- Token-to-tenant allowlists from either:
  - `KABUTO_API_TOKENS_JSON`, a JSON object mapping token values to tenant ID lists; or
  - `KABUTO_API_TOKENS_CONFIG`, a YAML/JSON path containing `tokens` entries with `token_env` and `tenant_ids`.
- Predictable error envelopes using `{"detail":{"error":"...","message":"..."}}`.

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Observed validation summary:

```text
59 passed, 1 warning in 2.91s
All checks passed!
Success: no issues found in 17 source files
```

The warning was from FastAPI/Starlette TestClient compatibility messaging:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## Tests Added

`tests/test_export_rest_api.py` adds deterministic fixture-backed endpoint coverage for:

- app import/factory and `/healthz`;
- PR throughput endpoint filters, pagination, and response fields;
- PR cycle-time endpoint filters and response fields;
- summary endpoint response fields;
- missing token `401`;
- invalid token `401`;
- disallowed tenant `403`;
- tenant A token blocked from tenant B and tenant B data absent from tenant A responses;
- YAML config path with `token_env` references instead of committed token values;
- query validation mapped to predictable `400` JSON.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md` because the implementation satisfies the REST API, auth, tenant isolation, documentation, and validation acceptance criteria.

## Limits

This evidence does not prove production OAuth/SSO, hosted deployment, rate limiting, audit logging, or production security hardening. Token config is intentionally local and minimal for the portfolio milestone. MCP tools were not implemented in this ticket.
