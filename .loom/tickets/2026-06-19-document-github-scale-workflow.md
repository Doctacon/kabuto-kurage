Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/tickets/2026-06-19-add-github-initial-lookback-window.md, .loom/tickets/2026-06-19-add-github-scale-tenant-config.md

# Document GitHub Scale Workflow

## Scope

Document and add Taskfile ergonomics for running the project in small/default mode versus opt-in portfolio-scale mode.

This ticket does not change the data model. It makes the workflow understandable and safe for a reviewer/operator.

## Documentation Requirements

Updated `README.md`, `docs/development.md`, `docs/dagster-asset-graph.md`, and `docs/github-bronze-ingestion.md` to explain:

- small default config is for everyday development;
- scale config is opt-in via `KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml`;
- scale first run should use `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180`;
- subsequent runs use incremental cursor state and `KABUTO_GITHUB_INCREMENTAL_LOOKBACK_DAYS`;
- how to materialize one scale tenant safely;
- how to inspect scale observability;
- how to avoid printing/committing the Proton Pass PAT.

## Taskfile Ergonomics

Added:

```bash
task materialize-scale TENANT=oss_orchestration
task observe-scale TENANT=oss_orchestration
```

`materialize-scale` sets `KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml` and defaults `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180` when not already set.

`observe-scale` sets `KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml`.

## Acceptance Criteria

- Docs clearly distinguish small default versus portfolio-scale mode.
- Docs include safe copy/paste commands for one-tenant scale runs.
- Docs explain staged validation before full scale materialization.
- If Taskfile aliases are added, deterministic tests validate them and ensure no secret echoing.
- Validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Current State

Done. Evidence recorded in `.loom/evidence/2026-06-19-github-scale-workflow-docs-validation.md`.

## Progress and Notes

- 2026-06-19: Opened as child ticket. Should run after config/interface details are known.
- 2026-06-19: Set active after scale config and initial lookback support were available.
- 2026-06-19: Added Taskfile `materialize-scale` and `observe-scale` aliases.
- 2026-06-19: Updated README and docs for opt-in scale workflow.
- 2026-06-19: Ran docs/task tests and Taskfile dry-runs successfully.

## Results

Acceptance criteria satisfied.

## Blockers

None.
