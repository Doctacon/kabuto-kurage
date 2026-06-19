Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Target: .loom/tickets/2026-06-18-add-minimal-mcp-wrapper.md
Verdict: pass

# Minimal MCP Wrapper Review

## Target

Current uncommitted implementation of `.loom/tickets/2026-06-18-add-minimal-mcp-wrapper.md`, including:

- `src/kabuto_kurage/mcp_server.py`
- `tests/test_export_mcp_wrapper.py`
- `docs/export-api.md`
- `README.md`
- `docs/architecture.md`
- `tests/test_export_api_docs.py`
- dependency updates in `pyproject.toml` and `uv.lock`

## Findings

### Pass: Tool surface is intentionally narrow

`create_mcp_server()` registers exactly:

- `github_pr_throughput_daily`
- `github_pr_cycle_time`
- `github_metrics_summary`

`tests/test_export_mcp_wrapper.py` asserts the MCP server's listed tool names match `MCP_TOOL_NAMES` and that each schema requires `tenant_id` and `api_token`.

### Pass: Auth behavior shares REST semantics

Each tool calls `_authorize_tool_call()`, which calls REST's existing `require_tenant_access()` helper with a bearer authorization header built from the `api_token` argument. This preserves the same token registry, tenant ID validation, missing/invalid token errors, and disallowed-tenant behavior as REST.

### Pass: Query/output contract stays aligned with REST

Each tool calls the shared query-layer functions used by REST:

- `query_pr_throughput_daily()`
- `query_pr_cycle_time()`
- `summarize_github_metrics()`

The exposed tool arguments mirror the corresponding REST/query filters.

### Pass: Tests cover acceptance-relevant behavior

The new deterministic tests cover:

- exact MCP tool list;
- required tool inputs;
- allowed tenant query results;
- missing token;
- invalid token;
- disallowed tenant;
- cross-tenant data non-leakage;
- absence of raw `payload_json`, raw `source`, and token values in outputs.

### Pass: Documentation keeps Jellyfish boundary cautious

Docs describe the MCP wrapper as a local learning analogue to Jellyfish's public MCP pattern. They explicitly avoid claiming Jellyfish compatibility, reproduction of Jellyfish proprietary metrics, or knowledge of Jellyfish's internal implementation.

## Verdict

Pass. The implementation satisfies the minimal MCP wrapper ticket and acceptance contract.

## Residual Risk

- The MCP wrapper is validated at the FastMCP tool registration/function layer, not through an external MCP Inspector or third-party client.
- The API token is an explicit MCP tool argument for local learning simplicity. That is acceptable for this milestone but is not production-grade MCP authorization.
- Existing suite still emits one Starlette/FastAPI TestClient deprecation warning unrelated to the MCP wrapper.
