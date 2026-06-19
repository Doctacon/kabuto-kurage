Status: open
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

## Progress and Notes

- Not started.

## Blockers

- Requires metrics layer to know what can be exported.
