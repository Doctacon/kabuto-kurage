Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-validate-tenant-isolation.md

# Tenant Isolation Validation Evidence

## What Was Observed

Implemented explicit tenant-isolation validation across the local GitHub bronze, silver, and gold layers.

Changed files:

- `src/kabuto_kurage/transforms/github_silver.py`
- `src/kabuto_kurage/transforms/github_gold.py`
- `tests/test_tenant_isolation.py`
- `docs/tenancy.md`
- `.loom/tickets/2026-06-18-validate-tenant-isolation.md`

Behavior added:

- Silver materialization now refuses to build a tenant's silver tables if the tenant-scoped bronze Delta path contains rows with another `tenant_id`.
- Gold materialization now refuses to build a tenant's gold metric tables if the tenant-scoped silver Delta path contains rows with another `tenant_id`.
- End-to-end tests seed distinct `sandbox` and `personal` fixture data, materialize silver and gold for both tenants, and assert tenant-specific tables/metrics exclude the other tenant's repositories and PR numbers.

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

## Validation Output

`uv run pytest`:

```text
collected 33 items

tests/test_dagster_assets.py ..
tests/test_github_bronze_ingestion.py ....
tests/test_github_gold_metrics.py .....
tests/test_github_silver_models.py .....
tests/test_scaffold.py ...
tests/test_tenancy.py ...........
tests/test_tenant_isolation.py ...

33 passed in 2.67s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 11 source files
```

`tests/test_tenant_isolation.py` specifically validates:

- Two-tenant fixture data exists for `sandbox` and `personal`.
- Bronze, silver, and gold Delta tables for each tenant contain only that tenant's `tenant_id`.
- `sandbox` gold cycle-time metrics include only `octocat/Hello-World` PR numbers `{1, 2}` and exclude `personal` data.
- `personal` gold cycle-time metrics include only `crlough/kabuto-kurage` PR number `{7}` and exclude `sandbox` data.
- Throughput metrics are tenant-scoped by repository and opened counts.
- Silver materialization fails closed on mismatched bronze `tenant_id` rows.
- Gold materialization fails closed on mismatched silver `tenant_id` rows.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-validate-tenant-isolation.md` because automated tests now validate tenant ID propagation across bronze/silver/gold layers and tenant-scoped metrics exclude the other tenant's data.

## Limits

This evidence proves local logical isolation in the current filesystem-backed Delta pipeline. It does not prove production authentication, authorization, encryption, row-level security, audit controls, or compute/network isolation.
