Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/tickets/2026-06-19-add-github-initial-lookback-window.md, .loom/tickets/2026-06-19-add-github-scale-tenant-config.md

# Document GitHub Scale Workflow

## Scope

Document and, if useful, add Taskfile ergonomics for running the project in small/default mode versus opt-in portfolio-scale mode.

This ticket should not change the data model. It makes the workflow understandable and safe for a reviewer/operator.

## Documentation Requirements

Update relevant docs such as `README.md`, `docs/development.md`, `docs/dagster-asset-graph.md`, and/or `docs/github-bronze-ingestion.md` to explain:

- small default config is for everyday development;
- scale config is opt-in via `KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml`;
- scale first run should use `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180`;
- subsequent runs use incremental cursor state and `KABUTO_GITHUB_INCREMENTAL_LOOKBACK_DAYS`;
- how to materialize one scale tenant safely;
- how to run a subset before a full scale backfill;
- how to inspect scale observability;
- how to avoid printing/committing the Proton Pass PAT.

## Optional Taskfile Ergonomics

If it improves clarity, add explicit tasks or examples such as:

```bash
task materialize-scale TENANT=oss_dagster
task observe-scale TENANT=oss_dagster
```

These should set or document the scale config and 180-day initial lookback without hiding secrets or surprising users.

## Acceptance Criteria

- Docs clearly distinguish small default versus portfolio-scale mode.
- Docs include safe copy/paste commands for one-tenant scale runs.
- Docs explain staged validation before full scale materialization.
- If Taskfile aliases are added, deterministic tests validate them and ensure no secret echoing.
- Validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Progress and Notes

- 2026-06-19: Opened as child ticket. Should run after config/interface details are known.

## Blockers

Blocked on scale config and initial lookback interface.
