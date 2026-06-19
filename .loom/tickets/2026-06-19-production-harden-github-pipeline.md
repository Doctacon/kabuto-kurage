Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-configure-live-github-portfolio-tenants.md

# Production-Harden GitHub Pipeline

## Scope

Implement production-looking upgrades the user wants to keep:

1. Dagster asset checks / data quality checks.
2. Incremental GitHub sync instead of always full PR scans.
3. Fine-grained PAT auth through `GITHUB_TOKEN`/`GH_TOKEN`.
4. Dagster schedules and retry policy.

GitHub App auth was briefly implemented, but the user decided not to create a GitHub App and asked to remove that path to keep the project simpler and aligned with the actual demo flow.

## Acceptance Criteria

- Dagster definitions include asset checks that validate table existence, non-empty tables where expected, tenant isolation, and required columns.
- GitHub PR ingestion persists an incremental cursor and uses a lookback-aware updated-at cutoff to avoid full historical scans after the first run while preserving prior bronze rows.
- GitHub authentication uses fine-grained PAT/env-token auth with clear `GITHUB_TOKEN`/`GH_TOKEN` secret handling.
- Dagster definitions include a retry policy and stopped-by-default schedule for local production-style orchestration.
- Docs and tests cover the kept behavior.
- Validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Journal

- 2026-06-19: Created after user requested upgrades 1, 2, 3, and 4.
- 2026-06-19: Added `delta_table_health` asset checks for all six GitHub assets.
- 2026-06-19: Added `github_assets_job` retry policy and stopped-by-default six-hour schedule.
- 2026-06-19: Added incremental PR cursor state and merge-preserving bronze writes.
- 2026-06-19: Removed GitHub App auth after user clarified they do not want to create a GitHub App.
- 2026-06-19: Updated docs, env example, deterministic tests, and live validation evidence.
- 2026-06-19: Recorded validation in `.loom/evidence/2026-06-19-production-hardening-validation.md`.

## Results

Acceptance criteria satisfied:

- Dagster definitions include checks for all six GitHub assets.
- Incremental PR sync writes `.local/data/dlt/github/{tenant_id}/incremental_state.json` and preserves existing bronze rows by `source_id`.
- GitHub auth uses `GITHUB_TOKEN`/`GH_TOKEN`; token values remain outside git.
- Dagster includes retry policy and stopped schedule.
- Documentation and `.env.example` describe the kept knobs.
- Validation passed: `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.
- Live PAT-backed materialization for `personal` succeeded after the changes.

## Blockers

None.
