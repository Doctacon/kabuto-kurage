Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/tickets/2026-06-19-add-github-initial-lookback-window.md, .loom/tickets/2026-06-19-add-github-scale-tenant-config.md, .loom/tickets/2026-06-19-document-github-scale-workflow.md

# Validate GitHub Scale Demo

## Scope

Run staged validation for the opt-in portfolio-scale GitHub corpus and record evidence.

This ticket is validation/evidence work. It should not broaden the scale corpus or change ingestion semantics except for small fixes discovered during validation, which should be tracked separately if non-trivial.

## Staged Validation Plan

### Stage 1: deterministic validation

Run:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

### Stage 2: metadata/access validation

Using the Proton Pass PAT as local `GITHUB_TOKEN` without printing it, validate that every repo in `config/tenants.scale.yaml` is reachable through GitHub metadata endpoints.

### Stage 3: small live scale subset

Materialize 2 representative scale tenants with:

```bash
export KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml
export KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180
task materialize TENANT=<tenant_id>
task observe TENANT=<tenant_id>
```

### Stage 4: optional full scale run

Only run the full scale materialization/backfill if the operator explicitly accepts the time/API cost.

## Acceptance Criteria

- Evidence record exists under `.loom/evidence/` with all validation commands and outputs summarized.
- Deterministic validation passes.
- GitHub metadata/access check covers all scale repositories without printing tokens.
- At least 2 representative scale tenants materialize successfully, unless blocked by GitHub rate limits or repo-specific failures that are recorded.
- Observability output shows non-zero rows for the representative materialized tenants, or explains why a selected repo had no PR activity in the 180-day window.
- Any full scale run is explicitly opt-in and recorded; absence of a full scale run is not treated as failure if subset validation passes.

## Current State

Done. Evidence recorded in `.loom/evidence/2026-06-19-github-scale-demo-validation.md`.

## Progress and Notes

- 2026-06-19: Opened as final child ticket for staged validation.
- 2026-06-19: Set active after scale config, initial lookback, and docs/workflow tickets were done.
- 2026-06-19: Re-authenticated Proton Pass session after it expired; token was not printed.
- 2026-06-19: Live materialized `oss_ingestion` and `oss_api_frameworks` with `task materialize-scale` and observed non-zero bronze/silver/gold row counts.
- 2026-06-19: Ran full deterministic validation: ruff, mypy, and pytest all passed.
- 2026-06-19: Deferred full 25-tenant scale materialization as an explicit operator-triggered action.

## Results

Acceptance criteria satisfied.

## Blockers

None.
