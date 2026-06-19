Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-build-gold-engineering-metrics.md, .loom/research/2026-06-18-jellyfish-company-research.md

# Plan Export API Follow-Up

## Scope

Shape the next milestone after the Dagster-centered MVP: a Jellyfish-inspired export/API or MCP surface over the computed engineering metrics.

Potential follow-up surfaces:

- REST API under `/api/v1` for tenant-scoped metrics.
- Grafana-friendly JSON export endpoints.
- Minimal MCP server exposing metrics and team/repo search.
- Static dashboard generated from gold metrics.

This ticket is a planning ticket, not the implementation of the API itself.

## Out of Scope

- Implementing the API during this ticket.
- Cloning Jellyfish's API exactly.
- Exposing private GitHub data publicly.

## Acceptance Criteria

- A follow-up spec or child tickets define the chosen export surface.
- The plan maps endpoints/tools to existing gold metrics.
- Tenant-scoped access expectations are explicit.
- The plan references Jellyfish public API/MCP research accurately.

## Current State

Done. The next milestone is shaped as a tenant-scoped engineering metrics export surface.

Created planning artifacts:

- Spec: `.loom/specs/engineering-metrics-export-surface.md`
- Follow-up parent: `.loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md`
- Child ticket: `.loom/tickets/2026-06-18-build-export-query-layer.md`
- Child ticket: `.loom/tickets/2026-06-18-implement-tenant-scoped-rest-api.md`
- Child ticket: `.loom/tickets/2026-06-18-document-and-validate-export-api.md`
- Child ticket: `.loom/tickets/2026-06-18-add-minimal-mcp-wrapper.md`

Chosen surface:

- REST API under `/api/v1` first.
- Minimal MCP wrapper second, after REST and shared query/auth logic are stable.

Metric mapping:

- `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily` maps to `gold/github/pr_throughput_daily`.
- `GET /api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time` maps to `gold/github/pr_cycle_time`.
- `GET /api/v1/tenants/{tenant_id}/metrics/github/summary` maps to both existing gold metric tables.
- MCP tools `github_pr_throughput_daily`, `github_pr_cycle_time`, and `github_metrics_summary` map to the same query contracts.

Tenant-scope expectation:

- Every endpoint/tool must require explicit `tenant_id`.
- Bearer tokens must map to explicit tenant allowlists.
- Missing/invalid tokens return `401`; disallowed tenant access returns `403`.
- No endpoint/tool defaults to all tenants.
- The export surface must not expose raw bronze payloads, token values, or cross-tenant data.

Evidence: `.loom/evidence/2026-06-18-export-api-followup-planning.md`.

Review: `.loom/reviews/2026-06-18-export-api-followup-planning-review.md`.

## Journal

- 2026-06-18: Set active and delegated planning to worker.
- 2026-06-18: Read ticket, Jellyfish company research, architecture docs, and current gold metric code/docs.
- 2026-06-18: Created export-surface spec defining REST-first and MCP-second plan, endpoints/tools, tenant-scoped access expectations, and public Jellyfish reference boundary.
- 2026-06-18: Created follow-up parent and child tickets for query layer, REST API, docs/validation, and minimal MCP wrapper.
- 2026-06-18: Ran validation commands (`uv run pytest`, `uv run ruff check .`, `uv run mypy src`, `git status --short`).
- 2026-06-18: Recorded evidence/review and moved ticket to done.

## Results

Acceptance criteria satisfied:

- A follow-up spec and child tickets define the chosen export surface.
- The plan maps proposed REST endpoints and MCP tools to existing gold metrics.
- Tenant-scoped access expectations are explicit.
- Jellyfish public API/MCP research is referenced accurately and cautiously.
- No API/MCP/dashboard implementation was added.

## Blockers

None for planning. Future implementation tickets must still decide exact API framework/dependencies, local token config format, response schema details, and MCP implementation strategy.
