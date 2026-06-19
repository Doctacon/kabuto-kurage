Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-18-add-minimal-mcp-wrapper.md, .loom/specs/engineering-metrics-export-surface.md

# Minimal MCP Wrapper Validation

## What Was Observed

Implemented a minimal local MCP wrapper in `src/kabuto_kurage/mcp_server.py` using the open-source MCP Python SDK (`mcp`). The wrapper registers exactly these initial metric tools:

- `github_pr_throughput_daily`
- `github_pr_cycle_time`
- `github_metrics_summary`

The tool functions require explicit `tenant_id` and `api_token` arguments, call the same auth helper used by REST (`require_tenant_access` in `src/kabuto_kurage/api/auth.py`), and read from the same shared gold-metric query layer (`src/kabuto_kurage/queries/github_metrics.py`).

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Observed output summary:

```text
67 passed, 1 warning in 3.66s
All checks passed!
Success: no issues found in 18 source files
```

`git status --short` showed the expected uncommitted implementation/docs/test/Loom changes and no staged files.

## Procedure

- Added MCP SDK dependency with `uv add 'mcp>=1.0.0'`.
- Added `src/kabuto_kurage/mcp_server.py` with `create_mcp_server()` and three registered tools.
- Added deterministic fixture-backed tests in `tests/test_export_mcp_wrapper.py`.
- Updated export docs and portfolio docs to document REST + MCP export surfaces and the Jellyfish public-reference boundary.
- Updated docs tests to assert MCP tool names, setup command, token argument, and anti-compatibility claims.
- Ran full pytest, ruff, and mypy validation.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-add-minimal-mcp-wrapper.md` because:

- MCP exposes only the three initial metric tools.
- Tool inputs and outputs map directly to the REST/query contract.
- Token allowlist behavior is shared with REST and covered for allowed, missing, invalid, and disallowed tenant cases.
- Fixture-backed tests verify tenant A cannot read tenant B data and responses do not include raw bronze payloads, `source`, or token values.
- Docs explain the MCP wrapper as a local learning analogue to Jellyfish's public MCP pattern, not a clone or compatibility target.

## Limits

This evidence does not prove compatibility with any specific MCP client beyond the MCP Python SDK server/tool registration layer. It does not prove production auth/security, hosted MCP deployment, or browser/inspector-based manual testing. The pytest warning is a known Starlette/FastAPI TestClient deprecation warning from existing REST API tests and is not introduced by the MCP wrapper behavior.
