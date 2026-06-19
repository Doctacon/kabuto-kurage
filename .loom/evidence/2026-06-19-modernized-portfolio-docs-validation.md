Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-update-modernized-portfolio-docs.md, .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md

# Modernized Portfolio Docs Validation

## What Was Observed

Portfolio-facing docs were updated after the storage profile, dlt-native bronze, DuckDB query, and Taskfile implementation tickets landed.

Changed documentation and tests:

- `README.md` now describes portable storage profiles, dlt source/resources and schema/state artifacts, DuckDB-backed REST/MCP exports, Taskfile workflow, and Proton Pass/env-var secret handling.
- `docs/architecture.md` now shows dlt source/resource ingestion, storage profiles, DuckDB query execution, Taskfile workflow, and the unchanged Jellyfish boundary.
- `docs/github-bronze-ingestion.md` now documents dlt source/resources, schema/state artifacts, Taskfile ingestion commands, storage-profile behavior, and secret handling.
- `docs/stack-validation.md` now documents `task validate-stack` and safe secret workflow for object-store profiles.
- `docs/export-api.md` now documents Taskfile API/MCP commands and DuckDB/storage-profile query behavior.
- `docs/local-iac.md` clarifies that storage profiles exist but local IaC does not provision MinIO/R2 services or secrets.
- `docs/development.md` now includes storage-profile setup shapes and reiterates Proton Pass/env-var handling.
- `tests/test_modernized_portfolio_docs.py` was added for docs coverage of storage profiles, dlt-native ingestion, DuckDB query layer, Taskfile workflow, secret handling, and Jellyfish boundary.
- `tests/test_portfolio_docs.py` was updated from the old `dlt REST helpers/extraction` wording to the implemented `dlt source/resources` wording.

Validation commands run:

```bash
uv run pytest tests/test_modernized_portfolio_docs.py -q
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Observed output summary:

```text
uv run pytest tests/test_modernized_portfolio_docs.py -q: 3 passed in 0.01s
uv run pytest: 84 passed, 2 warnings in 4.54s
uv run ruff check .: All checks passed!
uv run mypy src: Success: no issues found in 18 source files
git status --short: expected uncommitted docs/test/Loom changes only
```

Warnings observed during full pytest:

- FastAPI/Starlette deprecation warning from `fastapi.testclient` about future `httpx2` behavior.
- dlt runtime warning that `XDG_DATA_HOME` is set while `~/.dlt` already exists; dlt selected `~/.dlt`.

Neither warning failed validation.

## Procedure

The docs were checked against the implemented code and recent evidence for storage profiles, dlt-native bronze, DuckDB query layer, and Taskfile workflow. Deterministic documentation tests assert the key architecture claims and forbid common token/secret examples and unverified Jellyfish-internal claims.

## What This Supports or Challenges

Supports the ticket acceptance criteria:

- Docs accurately reflect storage profiles, dlt-native ingestion, DuckDB query layer, and Taskfile commands.
- Docs preserve public-Jellyfish inspiration boundaries and avoid claiming internals.
- Docs use placeholder-only secret shapes and do not include real token/account/key values.
- Documentation tests were added/updated.
- Full test/lint/typecheck validation passes.

## Limits

This evidence does not prove live MinIO/R2 service access, live GitHub ingestion, live Dagster UI clicks, or manual Task binary execution. It validates docs and deterministic tests only; live integrations still require local credentials exported safely from Proton Pass or another secret manager.
