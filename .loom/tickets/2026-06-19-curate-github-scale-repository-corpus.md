Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/specs/github-portfolio-scale-demo.md, .loom/decisions/github-scale-demo-many-tenant-opt-in.md

# Curate GitHub Scale Repository Corpus

## Scope

Create the candidate repository corpus for `config/tenants.scale.yaml`.

The corpus should include roughly 20-30 tenant partitions and 45-60 public repositories across at least 24 distinct owners/orgs where practical. It should mix open-source stack projects and broader engineering org projects.

This ticket is research/curation only. Do not add the config file in this ticket unless the parent explicitly merges the work into implementation. Produce a proposed tenant/repository table and evidence for why the list is safe and useful.

## Candidate Categories

Include a curated mix from areas such as:

- orchestration/data platforms: Dagster, Airflow, dbt, dlt;
- analytical engines/storage: DuckDB, Delta, Polars, Apache Arrow/Iceberg/DataFusion;
- API/product engineering: FastAPI, Pydantic, Starlette, Uvicorn;
- observability/infra: Grafana, Prometheus, OpenTelemetry, Kubernetes-adjacent tooling;
- broad engineering orgs with meaningful PR activity and public repos.

Avoid repos that are likely to dominate API usage or runtime without adding portfolio value.

## Acceptance Criteria

- Proposed corpus contains 20-30 tenant IDs and 45-60 `owner/repo` entries.
- Proposed corpus has at least 24 distinct owners/orgs, or explains why the final number is lower.
- Every repository is public and reachable via GitHub API metadata check using the local PAT from Proton Pass without printing the token.
- For each repo, capture non-secret metadata relevant to curation: private/archive status, default branch, approximate open issue count, and a rough recent-activity signal if available.
- Repositories with obvious risk are removed or marked as deferred with reasons.
- Output includes the exact YAML-ready tenant/repo list for the implementation ticket.
- Record evidence under `.loom/evidence/` with the metadata check results and limits.

## Progress and Notes

- 2026-06-19: Opened as first child of the portfolio-scale plan.

## Blockers

None.
