Status: done
Created: 2026-06-18
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md
Depends-On: .loom/tickets/2026-06-18-document-and-validate-export-api.md, .loom/specs/engineering-metrics-export-surface.md

# Add Minimal MCP Wrapper

## Scope

Add a minimal MCP server over the stable export query/API contract after REST is implemented and documented.

Initial tools from `.loom/specs/engineering-metrics-export-surface.md`:

- `github_pr_throughput_daily`
- `github_pr_cycle_time`
- `github_metrics_summary`

Each tool must require explicit `tenant_id` and enforce the same tenant allowlist behavior as the REST API, either by calling the REST service or by sharing the same query/auth layer.

## Out of Scope

- Reproducing Jellyfish's MCP implementation or exact tool names.
- Adding broad agent features beyond the three metric tools.
- Exposing raw GitHub payloads or private local data.

## Acceptance Criteria

- MCP server exposes only the initial three metric tools.
- Tool inputs and outputs map directly to the REST/query contract.
- Tenant access rules match REST behavior and are tested.
- Docs explain this as a local learning analogue to Jellyfish's public MCP pattern, not a clone of Jellyfish internals.

## Progress and Notes

- 2026-06-19: Added `src/kabuto_kurage/mcp_server.py` using the open-source MCP Python SDK.
- 2026-06-19: Registered exactly `github_pr_throughput_daily`, `github_pr_cycle_time`, and `github_metrics_summary`.
- 2026-06-19: Reused REST/query auth semantics by requiring explicit `tenant_id` and `api_token` and calling `require_tenant_access()`.
- 2026-06-19: Added deterministic fixture-backed MCP wrapper tests in `tests/test_export_mcp_wrapper.py`.
- 2026-06-19: Updated README, architecture, export docs, and docs tests for the MCP wrapper and public Jellyfish boundary.
- 2026-06-19: Validated with `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Current State

Done. Minimal local MCP wrapper is implemented over the stable query/auth layer.

## Journal

- 2026-06-18: Created as a future child of the export/API follow-up plan.
- 2026-06-18: Marked blocked pending export/API milestone selection, REST API completion, and export docs.
- 2026-06-18: REST API and export docs completed; moved to active and delegated minimal MCP wrapper implementation to worker.
- 2026-06-19: Implemented MCP wrapper, tests, docs, evidence, and review.
- 2026-06-19: Moved ticket to done after full validation passed.

## Results

Acceptance criteria satisfied:

- MCP server exposes only the initial three metric tools.
- Tool inputs and outputs map directly to the REST/query contract.
- Tenant access rules match REST behavior and are tested for allowed, missing, invalid, and disallowed tokens.
- Docs explain this as a local learning analogue to Jellyfish's public MCP pattern, not a clone of Jellyfish internals.
- MCP outputs do not expose raw bronze payloads, token values, or cross-tenant data.

Evidence: `.loom/evidence/2026-06-19-minimal-mcp-wrapper-validation.md`.

Review: `.loom/reviews/2026-06-19-minimal-mcp-wrapper-review.md`.

## Blockers

None.
