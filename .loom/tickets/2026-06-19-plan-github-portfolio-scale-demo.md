Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: none
Depends-On: .loom/decisions/github-scale-demo-many-tenant-opt-in.md, .loom/specs/github-portfolio-scale-demo.md

# Plan GitHub Portfolio-Scale Demo

## Scope

Coordinate the work needed to move the GitHub demo from a small correctness corpus to an opt-in portfolio-scale corpus that better justifies Dagster, dlt, Delta, incremental sync, asset checks, and tenant-scoped observability.

The plan implements the behavior in `.loom/specs/github-portfolio-scale-demo.md` and follows `.loom/decisions/github-scale-demo-many-tenant-opt-in.md`.

This parent ticket is an orchestration plan. Child tickets are the executable units.

## Desired Outcome

The project has two clear operating modes:

1. **Small default mode** using `config/tenants.example.yaml` for quick development and deterministic tests.
2. **Portfolio-scale mode** using `config/tenants.scale.yaml` with 25 tenants and 50 public repositories across 42 owners/orgs, with first-run history bounded to 180 days.

## Child Tickets and Status

### 1. Curate scale repository corpus

Ticket: `.loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md`

Status: done.

Produced 25 tenant IDs, 50 repositories, 42 distinct owners/orgs, and metadata/access evidence for every repository.

### 2. Add initial lookback support

Ticket: `.loom/tickets/2026-06-19-add-github-initial-lookback-window.md`

Status: done.

Added `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180` behavior and deterministic tests proving first-run page limiting.

### 3. Add scale tenant config and deterministic validation

Ticket: `.loom/tickets/2026-06-19-add-github-scale-tenant-config.md`

Status: done.

Added `config/tenants.scale.yaml` and deterministic shape tests.

### 4. Add scale workflow documentation and Taskfile ergonomics

Ticket: `.loom/tickets/2026-06-19-document-github-scale-workflow.md`

Status: done.

Added docs and Taskfile aliases `materialize-scale` and `observe-scale`.

### 5. Validate staged scale runs and record evidence

Ticket: `.loom/tickets/2026-06-19-validate-github-scale-demo.md`

Status: done.

Validated all repos through metadata checks and live materialized representative tenants `oss_ingestion` and `oss_api_frameworks`.

## Acceptance Criteria

- All child tickets are done or intentionally cancelled with reasons.
- The small default config remains the default and deterministic validation remains fast.
- `config/tenants.scale.yaml` exists and validates.
- First-run lookback support prevents unbounded initial full-history scale ingestion.
- Docs explain how to run scale mode safely.
- Evidence records what was live-validated and what remains optional.

## Current State

Done. All child tickets are closed with evidence.

## Progress and Notes

- 2026-06-19: Plan created from user direction: many tenants, mix OSS stack and engineering orgs, 180-day first-run bound, small default remains default.
- 2026-06-19: Drained all runnable child tickets in dependency order.
- 2026-06-19: Full deterministic validation passed: `uv run ruff check .`, `uv run mypy src`, `uv run pytest`.

## Results

Acceptance criteria satisfied.

## Blockers

None.
