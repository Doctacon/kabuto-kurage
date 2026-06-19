Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Target: .loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md
Verdict: pass

# Tenant-Scoped REST API Review

## Target

Reviewed the implementation of `.loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md`, including:

- `src/kabuto_kurage/api/app.py`
- `src/kabuto_kurage/api/auth.py`
- `tests/test_export_rest_api.py`
- `docs/export-api.md`
- dependency updates in `pyproject.toml` and `uv.lock`

## Findings

### Pass: endpoint surface matches the approved REST contract

The app exposes the three required endpoints under `/api/v1/tenants/{tenant_id}/metrics/github/...` and delegates metric reads to the existing query layer instead of duplicating gold table logic.

### Pass: tenant-scoped bearer auth is explicit

Bearer token auth maps token values to explicit tenant allowlists. The implementation supports environment JSON and a YAML/JSON config path that references token environment variables, keeping real token values outside committed config files.

### Pass: tenant isolation is tested at the API boundary

Endpoint tests cover allowed access, missing token, invalid token, disallowed tenant access, and tenant A being unable to read tenant B data. Responses are checked to avoid raw `payload_json`, internal `source`, and token-like fields.

### Pass: error shape is predictable

The API returns predictable JSON error envelopes for auth, authorization, tenant/query validation, missing tables, and malformed auth config.

### Pass: no MCP implementation was added

No MCP server or MCP tool code was added in this ticket.

## Verdict

Pass. The implementation satisfies the ticket acceptance criteria and is validated by the recorded test/lint/typecheck evidence.

## Residual Risk

- This is local bearer-token auth only; it is intentionally not production OAuth/SSO.
- The API currently returns plain JSON arrays/objects without Pydantic response models to avoid over-modeling the already-tested query-layer contract.
- FastAPI's TestClient emitted a third-party deprecation warning about future `httpx2` migration; it does not currently fail validation.
