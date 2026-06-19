Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-migrate-github-bronze-ingestion-to-dlt.md, .loom/decisions/use-dlt-for-github-ingestion.md

# dlt GitHub Bronze Ingestion Validation

## What Was Observed

GitHub bronze ingestion was migrated to use dlt REST extraction primitives while preserving the existing tenant-scoped Delta bronze table contract.

Changed implementation highlights:

- `pyproject.toml` and `uv.lock` now include `dlt>=1.28.0` as a runtime dependency.
- `src/kabuto_kurage/ingestion/github_bronze.py` now constructs dlt's `RESTClient` with `BearerTokenAuth` and `HeaderLinkPaginator` for GitHub API extraction.
- Existing bronze Delta schema, table paths, overwrite writes, result objects, rate-limit snapshots, and CLI entrypoint are unchanged.
- `tools/validate_stack.py` now validates GitHub API auth through dlt's REST client instead of direct `httpx` calls.
- README and docs now describe dlt as the GitHub ingestion layer.

Validation commands run:

```bash
uv lock
uv run pytest tests/test_github_bronze_ingestion.py -q
uv run ruff check src/kabuto_kurage/ingestion/github_bronze.py tests/test_github_bronze_ingestion.py
uv run mypy src
uv run pytest
uv run ruff check .
uv run mypy src
uv run python tools/validate_stack.py
```

Observed output summary:

```text
uv lock: added dlt v1.28.0 and transitive dependencies
uv run pytest tests/test_github_bronze_ingestion.py -q: 5 passed, 1 warning
uv run pytest: 68 passed, 2 warnings in 4.76s
uv run ruff check .: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
uv run python tools/validate_stack.py: Delta proof passed, Dagster proof passed, GitHub live auth skipped because no token was set
```

Warnings observed:

- FastAPI/Starlette deprecation warning from `fastapi.testclient` about future `httpx2` migration.
- dlt runtime warning that `XDG_DATA_HOME` is set while `~/.dlt` already exists; dlt selected `~/.dlt`.

Neither warning failed validation.

## Procedure

The migration was validated with deterministic tests that use a local `requests` adapter mounted into the dlt REST client. The adapter returns fixture GitHub responses, GitHub-style `Link` pagination headers, and rate-limit headers without live network calls.

The full suite was then run to verify downstream silver, gold, Dagster, REST API, MCP, observability, IaC, and documentation tests still pass without contract changes.

## What This Supports or Challenges

Supports the migration ticket acceptance criteria:

- GitHub API extraction now uses dlt `RESTClient` and `HeaderLinkPaginator`.
- Deterministic ingestion tests still prove pagination, rate-limit capture, raw payload retention, idempotent Delta writes, and no token leakage.
- README/docs identify dlt as the ingestion layer.
- Full downstream test suite passes.

## Limits

This evidence does not prove live GitHub extraction because no `GITHUB_TOKEN` or `GH_TOKEN` was present for `tools/validate_stack.py`; live auth was skipped as designed. It also does not move storage writes into dlt destinations; by decision, dlt owns extraction while the project preserves its existing Delta write path.
