Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/specs/github-portfolio-scale-demo.md, .loom/tickets/2026-06-19-production-harden-github-pipeline.md

# Add GitHub Initial Lookback Window

## Scope

Add support for bounding the first pull-request ingestion run for a tenant/repository when no incremental cursor exists yet.

Current incremental behavior avoids full rescans after cursor state exists, but the first run can still crawl all historical PRs. Scale mode needs an initial 180-day bound so the first materialization of ~50 repositories remains safe.

## Interface

Added:

```bash
KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180
```

Behavior:

- If no cursor exists for a repository and the env var is set, fetch PR pages sorted by `updated_at desc` and stop once page data falls before `fetched_at - lookback_days`.
- If a cursor exists, keep using the existing incremental cursor plus `KABUTO_GITHUB_INCREMENTAL_LOOKBACK_DAYS` safety window.
- If the env var is unset, preserve existing behavior for small/default workflows.
- Fixture mode remains deterministic and does not depend on wall-clock lookback behavior.

## Acceptance Criteria

- Implementation supports a configurable first-run lookback by days.
- Deterministic tests prove first-run ingestion stops before older PR pages and does not fetch all history when the initial lookback is set.
- Existing incremental cursor tests still pass.
- Existing small/default behavior is preserved when the env var is unset.
- Docs mention that scale mode should use `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180`.
- Validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Current State

Done. Evidence recorded in `.loom/evidence/2026-06-19-github-initial-lookback-validation.md`.

## Progress and Notes

- 2026-06-19: Opened as child ticket for portfolio-scale demo planning.
- 2026-06-19: Set active and implemented `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS` in `src/kabuto_kurage/ingestion/github_bronze.py`.
- 2026-06-19: Added deterministic test coverage proving a first-run lookback filters older PRs and avoids fetching linked older pages.
- 2026-06-19: Updated `.env.example`, `README.md`, and `docs/github-bronze-ingestion.md` with the new env var.
- 2026-06-19: Ran targeted tests, ruff, and mypy; all passed.

## Results

Acceptance criteria satisfied.

## Blockers

None.
