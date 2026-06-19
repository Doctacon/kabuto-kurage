Status: blocked
Created: 2026-06-18
Updated: 2026-06-18
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

- Not started.

## Current State

Blocked. This belongs to the export/API follow-up milestone, which is awaiting explicit operator/product selection, and it also depends on stable REST API and export docs.

## Journal

- 2026-06-18: Created as a future child of the export/API follow-up plan.
- 2026-06-18: Marked blocked pending export/API milestone selection, REST API completion, and export docs.

## Blockers

- Requires stable REST API and export docs.
- Requires operator/product decision to begin the export/API follow-up milestone.
