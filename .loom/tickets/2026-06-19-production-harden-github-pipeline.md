Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-configure-live-github-portfolio-tenants.md

# Production-Harden GitHub Pipeline

## Scope

Implement the user's requested production-looking upgrades:

1. Dagster asset checks / data quality checks.
2. Incremental GitHub sync instead of always full PR scans.
3. GitHub App auth support with PAT fallback.
4. Dagster schedules and retry policy.

## Acceptance Criteria

- Dagster definitions include asset checks that validate table existence, non-empty tables where expected, tenant isolation, and required columns.
- GitHub PR ingestion persists an incremental cursor and uses a lookback-aware updated-at cutoff to avoid full historical scans after the first run while preserving prior bronze rows.
- GitHub authentication supports fine-grained PAT/env token and GitHub App installation token minting from env vars/private key.
- Dagster definitions include a retry policy and stopped-by-default schedule for local production-style orchestration.
- Docs and tests cover the new behavior.
- Validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Journal

- 2026-06-19: Created after user requested upgrades 1, 2, 3, and 4.
- 2026-06-19: Added `delta_table_health` asset checks for all six GitHub assets.
- 2026-06-19: Added `github_assets_job` retry policy and stopped-by-default six-hour schedule.
- 2026-06-19: Added incremental PR cursor state and merge-preserving bronze writes.
- 2026-06-19: Added GitHub App installation-token auth with PAT/env-token fallback.
- 2026-06-19: Updated docs, env example, deterministic tests, and live validation evidence.
- 2026-06-19: Recorded validation in `.loom/evidence/2026-06-19-production-hardening-validation.md`.

## Results

Acceptance criteria satisfied:

- Dagster definitions include checks for all six GitHub assets.
- Incremental PR sync writes `.local/data/dlt/github/{tenant_id}/incremental_state.json` and preserves existing bronze rows by `source_id`.
- GitHub auth supports `KABUTO_GITHUB_AUTH_MODE=auto|pat|app`, PAT env tokens, and GitHub App installation-token minting.
- Dagster includes retry policy and stopped schedule.
- Documentation and `.env.example` describe the new knobs.
- Validation passed: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.
- Live PAT-backed materialization for `personal` succeeded after the changes.

## Blockers

None. Live GitHub App validation remains optional and requires user-created GitHub App credentials.
