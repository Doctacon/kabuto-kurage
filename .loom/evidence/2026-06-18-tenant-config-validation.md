Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-model-tenants-and-source-config.md

# Tenant Config Validation Evidence

## What Was Observed

Implemented tenant/source configuration without implementing GitHub ingestion.

Changed files:

- `config/tenants.example.yaml`
- `src/kabuto_kurage/tenancy.py`
- `src/kabuto_kurage/paths.py`
- `tests/test_tenancy.py`
- `docs/tenancy.md`
- `README.md`
- `.env.example`
- `.gitignore`
- `pyproject.toml`
- `uv.lock`
- `.loom/tickets/2026-06-18-model-tenants-and-source-config.md`

## Procedure

Validation commands run from the repository root:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
uv run python -c "from kabuto_kurage.tenancy import load_tenant_registry; print(load_tenant_registry().tenant_ids)"
git status --short
```

## Validation Output

`uv sync` completed successfully after adding `pyyaml` to runtime dependencies.

`uv run pytest`:

```text
collected 14 items

tests/test_scaffold.py ...                                               [ 21%]
tests/test_tenancy.py ...........                                        [100%]

14 passed in 0.05s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 4 source files
```

Tenant registry sanity command:

```text
('personal', 'sandbox')
```

`git status --short` showed only expected modified/untracked files for this ticket; no staged files.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-model-tenants-and-source-config.md` because:

- The committed YAML registry defines two tenants with GitHub source configuration.
- The Python loader validates tenant IDs, duplicate tenant IDs, missing GitHub sources, repository shape, and secret-reference mistakes.
- The path helpers define tenant-scoped Delta storage conventions.
- Documentation explains the local tenancy model, secret references, storage paths, alternatives, and limitations.

## Limits

This evidence does not prove real GitHub API ingestion, raw/silver/gold Delta writes, Dagster asset behavior, or production-grade security. Those are deferred to downstream tickets.
