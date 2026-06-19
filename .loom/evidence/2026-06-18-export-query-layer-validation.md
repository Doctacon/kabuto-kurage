Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-build-export-query-layer.md, .loom/specs/engineering-metrics-export-surface.md

# Export Query Layer Validation

## What Was Observed

Implemented and validated a shared Python query layer over existing tenant-scoped GitHub gold Delta tables.

Changed implementation files:

- `src/kabuto_kurage/queries/__init__.py`
- `src/kabuto_kurage/queries/github_metrics.py`

Changed test files:

- `tests/test_export_github_metrics.py`

Updated Loom records:

- `.loom/tickets/2026-06-18-build-export-query-layer.md`
- `.loom/evidence/2026-06-18-export-query-layer-validation.md`
- `.loom/reviews/2026-06-18-export-query-layer-review.md`

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
grep -RInE 'FastAPI|APIRouter|@app\.|mcp|MCP' src tests || true
grep -RInEi 'payload_json|token' src/kabuto_kurage/queries tests/test_export_github_metrics.py || true
git status --short
```

Observed validation summary:

```text
51 passed in 3.02s
All checks passed!
Success: no issues found in 14 source files
No FastAPI/APIRouter/@app/MCP code found in src or tests.
Query/token grep found only negative test assertions for payload_json/token in tests/test_export_github_metrics.py.
```

`git status --short` showed unstaged/untracked changes and no staged files:

```text
 M .loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md
 M .loom/tickets/2026-06-18-build-export-query-layer.md
?? src/kabuto_kurage/queries/
?? tests/test_export_github_metrics.py
```

## Procedure

1. Added `kabuto_kurage.queries.github_metrics` with tenant-scoped functions:
   - `query_pr_throughput_daily`
   - `query_pr_cycle_time`
   - `summarize_github_metrics`
   - `serialize_json_value`
2. Added deterministic fixture-backed Delta tests that write gold Delta tables directly with existing gold schemas.
3. Validated date, repository, merged, limit, and offset filters.
4. Validated JSON serialization through `json.dumps` over query results and summary dicts.
5. Validated tenant ID errors, throughput and cycle-time missing-table errors, and mismatched tenant rows inside a tenant path.
6. Checked the diff did not add HTTP routes, MCP server/tools, or dashboard UI code.

## What This Supports or Challenges

Supports the acceptance criteria for `.loom/tickets/2026-06-18-build-export-query-layer.md`:

- Query functions read tenant-scoped gold Delta paths only.
- PR throughput rows can be filtered by date, repository, limit, and offset.
- PR cycle-time rows can be filtered by date, repository, merged status, limit, and offset.
- A compact summary is produced from both gold tables and reports `average_cycle_time_hours`.
- Invalid tenant IDs and missing gold tables fail clearly.
- Returned records and summary dictionaries are JSON-serializable.
- Tests prove returned fields omit `payload_json`, `source`, token-looking keys, and cross-tenant rows.
- No HTTP/MCP/dashboard surface was added.

## Limits

This evidence does not validate the future REST API, bearer-token authorization, MCP wrapper, or production-scale query performance. The query layer currently reads gold Delta tables into Python memory, which is acceptable for this local portfolio milestone but may need pushdown or a query engine for larger datasets.
