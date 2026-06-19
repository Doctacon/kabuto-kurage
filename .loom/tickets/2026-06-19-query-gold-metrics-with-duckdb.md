Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md

# Query Gold Metrics with DuckDB

## Scope

Replace the current Python in-memory export query implementation with DuckDB SQL over gold Delta tables.

Expected work:

- Add DuckDB dependency and a small query/session module if needed.
- Load/install required DuckDB extensions such as `delta` and object-store support where appropriate.
- Query `gold/github/pr_throughput_daily` and `gold/github/pr_cycle_time` through SQL.
- Express date/repository/merged filters, limits, offsets, and summary aggregation in SQL.
- Preserve REST/MCP response contracts and auth behavior.
- Keep tenant-scoped path validation before query execution.

## Out of Scope

- Changing REST endpoint paths or MCP tool names.
- Exposing raw bronze payloads.
- Cross-tenant query APIs.
- Performance tuning beyond correctness and local readability.

## Acceptance Criteria

- Query layer uses DuckDB SQL to read gold Delta tables.
- Existing REST/MCP tests pass or are adapted without changing public contracts.
- Tests prove tenant A cannot read tenant B data.
- Missing table and invalid filter errors remain predictable.
- DuckDB local Delta validation is covered by tests/evidence.
- Full test/lint/typecheck validation passes.

## Progress and Notes

- Not started.

## Blockers

- Requires storage profile conventions so DuckDB knows how to resolve table URIs and secrets.
