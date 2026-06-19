Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-document-github-scale-workflow.md

# GitHub Scale Workflow Docs Validation

## What Was Observed

Added documentation and Taskfile ergonomics for small/default mode versus opt-in portfolio-scale mode.

New Taskfile aliases:

```bash
task materialize-scale TENANT=oss_orchestration
task observe-scale TENANT=oss_orchestration
```

The aliases set or preserve:

```bash
KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml
KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180
```

without printing or interpolating secret values.

## Procedure

Ran deterministic docs/task tests and dry-runs:

```bash
uv run pytest tests/test_taskfile_workflow.py tests/test_portfolio_docs.py tests/test_modernized_portfolio_docs.py -q
task --dry materialize-scale TENANT=oss_orchestration
task --dry observe-scale TENANT=oss_orchestration OBSERVE_FORMAT=json
```

Observed:

```text
14 passed
```

Dry-run output showed the expected opt-in scale config and 180-day initial lookback for `materialize-scale`, and the expected scale config for `observe-scale`.

## What This Supports or Challenges

Supports that operators can safely distinguish small default development from portfolio-scale runs and can materialize/observe one scale tenant without manually remembering every environment variable.

## Limits

This evidence validates documentation/task structure only. Live scale materialization is handled by `.loom/tickets/2026-06-19-validate-github-scale-demo.md`.
