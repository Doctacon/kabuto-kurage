Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-validate-github-scale-demo.md, .loom/specs/github-portfolio-scale-demo.md

# GitHub Scale Demo Validation

## What Was Observed

The opt-in portfolio-scale GitHub workflow was validated in staged form.

## Stage 1: Deterministic Validation

Commands run:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

Observed:

```text
All checks passed!
Success: no issues found in 18 source files
91 passed, 3 warnings
```

## Stage 2: Metadata/Access Validation

Repository metadata/access validation for all 50 scale repositories is recorded in:

```text
.loom/evidence/2026-06-19-github-scale-corpus-curation.md
```

Summary from that evidence:

- Tenant partitions: 25
- Repositories: 50
- Distinct owners/orgs: 42
- Metadata/access errors: 0
- Private/archived/disabled accepted repos: 0
- Final observed GitHub core rate-limit remaining after curation checks: 4948 of 5000

## Stage 3: Representative Live Scale Materialization

Used the Proton Pass item `GitHub API Token`, field `API Key`, as a local `GITHUB_TOKEN` without printing the token.

Commands:

```bash
task materialize-scale TENANT=oss_ingestion
task observe-scale TENANT=oss_ingestion OBSERVE_FORMAT=json
task materialize-scale TENANT=oss_api_frameworks
task observe-scale TENANT=oss_api_frameworks OBSERVE_FORMAT=json
```

Observed:

```text
oss_ingestion RUN_SUCCESS
bronze/repositories: rows=2 freshness=fresh
bronze/pull_requests: rows=888 freshness=fresh
silver/repositories: rows=2 freshness=fresh
silver/pull_requests: rows=888 freshness=fresh
gold/pr_throughput_daily: rows=368 freshness=fresh
gold/pr_cycle_time: rows=888 freshness=fresh

oss_api_frameworks RUN_SUCCESS
bronze/repositories: rows=2 freshness=fresh
bronze/pull_requests: rows=1231 freshness=fresh
silver/repositories: rows=2 freshness=fresh
silver/pull_requests: rows=1231 freshness=fresh
gold/pr_throughput_daily: rows=434 freshness=fresh
gold/pr_cycle_time: rows=1231 freshness=fresh
```

These two tenants validate both a data-ingestion/tooling tenant (`oss_ingestion`: dlt + Meltano) and an API/framework tenant (`oss_api_frameworks`: FastAPI + Flask).

## Stage 4: Full Scale Run

A full 25-tenant / 50-repository materialization was intentionally deferred. The representative subset produced thousands of PR rows and validated the workflow without spending the full GitHub API/time budget. Full scale remains operator-triggered via repeated `task materialize-scale TENANT=...` runs or Dagster backfills.

## What This Supports or Challenges

Supports that the scale config is not merely theoretical: selected scale tenants materialize successfully with non-trivial row counts, and deterministic validation passes after the scale workflow changes.

## Limits

This evidence does not prove every scale tenant materializes end-to-end. It proves all repos were metadata-accessible and two representative tenants materialized successfully with the 180-day first-run bound. Full scale backfill remains an explicit operator action.
