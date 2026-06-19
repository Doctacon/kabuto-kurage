Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-build-silver-github-models.md

# GitHub Silver Models Evidence

## What Was Observed

Implemented stable silver GitHub repository and pull request models derived from tenant-scoped bronze Delta tables.

Changed implementation/docs/tests:

- `src/kabuto_kurage/transforms/__init__.py`
- `src/kabuto_kurage/transforms/github_silver.py`
- `tools/build_github_silver.py`
- `tests/test_github_silver_models.py`
- `docs/github-silver-models.md`
- `docs/development.md`
- `README.md`
- `.loom/tickets/2026-06-18-build-silver-github-models.md`

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

No live GitHub API calls were needed. Tests use representative bronze records built from fixture-like GitHub repository and pull request payloads, then materialize silver Delta tables under temporary data roots.

## Validation Output

`uv run pytest`:

```text
collected 23 items

tests/test_github_bronze_ingestion.py ....
tests/test_github_silver_models.py .....
tests/test_scaffold.py ...
tests/test_tenancy.py ...........

23 passed in 0.71s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 8 source files
```

`git status --short` showed only expected unstaged working-tree changes for this ticket and no staged files.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-build-silver-github-models.md` because:

- Silver `repositories` and `pull_requests` Delta tables are materialized from bronze Delta tables by `materialize_tenant_github_silver()`.
- Tenant identity is preserved in every silver record and tenant-specific Delta paths remain separate.
- Source traceability is preserved through `bronze_source_id`, `bronze_source_url`, `bronze_api_url`, payload IDs, and payload URLs.
- Typed stable columns are extracted for repository and pull request models.
- Missing/null payload fields are handled by nullable silver columns rather than transform failure.
- Deterministic tests cover representative repository and PR transforms, null/missing handling, Delta writes, and tenant path separation.
- `docs/github-silver-models.md` documents table columns, intended use, and schema-evolution behavior.

## Limits

This evidence does not prove gold metrics, Dagster asset graph integration, live GitHub ingestion, incremental silver merging, or every GitHub field. Those are intentionally out of scope for this ticket and tracked by downstream tickets.
