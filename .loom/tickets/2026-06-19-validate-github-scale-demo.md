Status: open
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

Record non-secret results: status, private flag, archived flag, default branch, and any rate-limit posture.

### Stage 3: small live scale subset

Materialize 2-3 representative scale tenants with:

```bash
export KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml
export KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180
task materialize TENANT=<tenant_id>
task observe TENANT=<tenant_id>
```

Pick at least one data-stack tenant and one broader engineering-org tenant.

### Stage 4: optional full scale run

Only run the full scale materialization/backfill if the operator explicitly accepts the time/API cost. If skipped, record that it was intentionally deferred and why.

## Acceptance Criteria

- Evidence record exists under `.loom/evidence/` with all validation commands and outputs summarized.
- Deterministic validation passes.
- GitHub metadata/access check covers all scale repositories without printing tokens.
- At least 2 representative scale tenants materialize successfully, unless blocked by GitHub rate limits or repo-specific failures that are recorded.
- Observability output shows non-zero rows for the representative materialized tenants, or explains why a selected repo had no PR activity in the 180-day window.
- Any full scale run is explicitly opt-in and recorded; absence of a full scale run is not treated as failure if subset validation passes.

## Progress and Notes

- 2026-06-19: Opened as final child ticket for staged validation.

## Blockers

Blocked on scale config, initial lookback support, and docs/workflow.
