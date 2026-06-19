Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-scaffold-portfolio-data-platform.md

# Scaffold Validation Evidence

## What Was Observed

The scaffold ticket created a Python `uv` project with source/test layout, developer tooling, ignored local-data/secrets paths, and README/development instructions.

Changed scaffold files included:

- `pyproject.toml`
- `uv.lock`
- `.python-version`
- `.gitignore`
- `.env.example`
- `src/kabuto_kurage/__init__.py`
- `src/kabuto_kurage/paths.py`
- `src/kabuto_kurage/definitions.py`
- `tests/test_scaffold.py`
- `README.md`
- `docs/development.md`

## Procedure

Validation commands run from the repository root:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run mypy src
uv run python -c "from kabuto_kurage.definitions import defs; print(type(defs).__name__)"
uv run python tools/validate_stack.py
git status --short
```

## Validation Output

`uv sync` completed successfully, created `.venv`, resolved dependencies, built the local package, and installed runtime/development dependencies.

`uv run pytest`:

```text
collected 3 items

tests/test_scaffold.py ... [100%]

3 passed in 0.03s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 3 source files
```

Dagster code-location import sanity:

```text
Definitions
```

`uv run python tools/validate_stack.py` continued to pass local Delta/Dagster validation, with live GitHub validation skipped because no token was present:

```json
{
  "dagster": { "asset": "toy_delta_stack_validation", "rows": 2, "status": "passed" },
  "delta": { "delta_log_files": ["00000000000000000000.json"], "rows": 2, "status": "passed", "version": 0 },
  "github": { "status": "skipped_missing_token" }
}
```

`git status --short` showed only expected unstaged scaffold/ticket/evidence changes and no staged files.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-scaffold-portfolio-data-platform.md` because:

- Dependency installation is documented and validated through `uv sync`.
- Tests, lint, and type-check commands exist and pass.
- README and `docs/development.md` document developer commands and current milestone.
- `.gitignore` excludes secret files and local generated data.
- The Dagster startup module exists without implementing downstream assets.

## Limits

This evidence does not prove real GitHub ingestion, tenant configuration, Delta table design, or Dagster asset graph behavior. Those are explicitly deferred to downstream child tickets.
