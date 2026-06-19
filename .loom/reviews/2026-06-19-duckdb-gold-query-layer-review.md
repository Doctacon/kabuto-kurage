Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Target: .loom/tickets/2026-06-19-query-gold-metrics-with-duckdb.md
Verdict: pass

# DuckDB Gold Query Layer Review

## Target

Review of the DuckDB migration for `src/kabuto_kurage/queries/github_metrics.py`, related export docs, and tests.

## Findings

### Pass: public REST/MCP contracts preserved

The FastAPI routes and MCP tool names were not changed. Existing REST and MCP tests continue to call:

- `/api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily`
- `/api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time`
- `/api/v1/tenants/{tenant_id}/metrics/github/summary`
- `github_pr_throughput_daily`
- `github_pr_cycle_time`
- `github_metrics_summary`

Targeted export/API/MCP tests passed.

### Pass: query work moved to DuckDB SQL

The query layer now uses DuckDB connections and `delta_scan(?)` for throughput rows, cycle-time rows, tenant mismatch checks, and summary aggregations. Filters, ordering, limit, and offset are represented in SQL rather than Python list filtering.

### Pass: tenant isolation remains fail-closed

The query layer still validates tenant IDs before table URI resolution and scans only the requested tenant's gold paths. It also checks for mismatched `tenant_id` values inside the tenant path before returning filtered results, preserving the previous fail-closed behavior.

### Pass: JSON response compatibility retained

Timestamp values returned by DuckDB are normalized to UTC ISO strings so existing response contracts remain stable. Raw bronze `payload_json`, internal `source`, and token fields are still excluded from exported records.

### Minor residual risk: live object-store query not exercised

The migration centralizes DuckDB extension/secret setup through storage profiles, but this ticket validated local filesystem Delta scans only. Live MinIO/R2 scans remain future environment-dependent validation.

## Verdict

Pass. The implementation satisfies the ticket acceptance criteria for local deterministic behavior and preserves public export contracts.

## Residual Risk

- DuckDB `delta_scan` against MinIO/R2 should be validated when object-store services/credentials are available.
- DuckDB extension installation may require network access the first time in a fresh environment unless extensions are pre-cached.
