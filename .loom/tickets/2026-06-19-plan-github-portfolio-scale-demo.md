Status: open
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
2. **Portfolio-scale mode** using `config/tenants.scale.yaml` with roughly 20-30 tenants and 45-60 public repositories across at least 24 owners/orgs, with first-run history bounded to 180 days.

## Child Tickets and Sequencing

### 1. Curate scale repository corpus

Ticket: `.loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md`

Purpose: produce the candidate list of tenants/repos and evidence that the list is accessible, relevant, and not pathological.

This should run first because implementation depends on the shape and size of the corpus.

### 2. Add initial lookback support

Ticket: `.loom/tickets/2026-06-19-add-github-initial-lookback-window.md`

Purpose: support `KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180` or equivalent so first scale runs do not crawl all historical PRs.

Can run in parallel with corpus curation after the spec is understood, but should be completed before full live scale materialization.

### 3. Add scale tenant config and deterministic validation

Ticket: `.loom/tickets/2026-06-19-add-github-scale-tenant-config.md`

Purpose: add `config/tenants.scale.yaml` and tests that validate shape, repo counts, owner counts, tenant ID safety, and lack of secrets.

Depends on the curated repository corpus.

### 4. Add scale workflow documentation and Taskfile ergonomics

Ticket: `.loom/tickets/2026-06-19-document-github-scale-workflow.md`

Purpose: make small default versus scale mode obvious, including safe commands, env vars, and staged validation workflow.

Depends on initial lookback support and scale config naming.

### 5. Validate staged scale runs and record evidence

Ticket: `.loom/tickets/2026-06-19-validate-github-scale-demo.md`

Purpose: run safe live validation with the Proton Pass PAT, first as repository accessibility checks, then a small subset of scale tenants, and optionally a full scale materialization if explicitly chosen.

Depends on all previous child tickets.

## Acceptance Criteria

- All child tickets are done or intentionally cancelled with reasons.
- The small default config remains the default and deterministic validation remains fast.
- `config/tenants.scale.yaml` exists and validates.
- First-run lookback support prevents unbounded initial full-history scale ingestion.
- Docs explain how to run scale mode safely.
- Evidence records what was live-validated and what remains optional.

## Progress and Notes

- 2026-06-19: Plan created from user direction: many tenants, mix OSS stack and engineering orgs, 180-day first-run bound, small default remains default.

## Blockers

None. Repo corpus curation is the first executable unit.
