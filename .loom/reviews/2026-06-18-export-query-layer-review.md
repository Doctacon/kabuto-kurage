Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Target: .loom/tickets/2026-06-18-build-export-query-layer.md, src/kabuto_kurage/queries/github_metrics.py, tests/test_export_github_metrics.py
Verdict: pass

# Export Query Layer Review

## Target

Reviewed the implementation of `.loom/tickets/2026-06-18-build-export-query-layer.md`:

- `src/kabuto_kurage/queries/github_metrics.py`
- `src/kabuto_kurage/queries/__init__.py`
- `tests/test_export_github_metrics.py`

## Findings

### Pass: tenant-scoped reads use existing path conventions

The query layer validates `tenant_id` through `validate_tenant_id` and resolves paths only through:

```python
delta_table_path(tenant_id, "gold", GITHUB_SOURCE, table_name)
```

This is consistent with the existing lakehouse path convention and does not introduce all-tenant reads.

### Pass: output fields are allowlisted

Both row query functions serialize only explicit export fields. Internal `source` is intentionally omitted, and raw bronze fields such as `payload_json` are not read or returned.

### Pass: deterministic tests cover filters and isolation

`tests/test_export_github_metrics.py` writes deterministic fixture-backed gold Delta tables and covers:

- throughput date/repository/limit/offset filtering;
- cycle-time date/repository/merged/limit/offset filtering;
- summary aggregation across both tables;
- tenant-scoped path separation;
- invalid tenant ID errors;
- missing gold table errors;
- mismatched tenant rows inside a tenant path.

### Pass: no out-of-scope surfaces added

A grep for FastAPI/APIRouter/app decorators/MCP terms in `src` and `tests` found no HTTP routes, MCP server/tools, or dashboard UI additions.

## Verdict

Pass. The implementation satisfies the query-layer ticket without implementing REST, MCP, or dashboard concerns.

## Residual Risk

- The query layer reads Delta tables into Python memory. This is acceptable for the local portfolio milestone and spec, but future larger datasets may need predicate pushdown, DuckDB, or another query engine.
- The summary uses `average_cycle_time_hours` rather than median. This is permitted by the spec but should be reflected in future API docs.
