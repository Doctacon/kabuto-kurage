Status: active
Created: 2026-06-19
Updated: 2026-06-19
Related-Decision: .loom/decisions/github-scale-demo-many-tenant-opt-in.md

# GitHub Portfolio-Scale Demo Spec

## Purpose and Scope

This spec defines an opt-in GitHub corpus and workflow that makes `kabuto-kurage` feel like a serious local engineering-intelligence data platform rather than a toy two-repository demo.

The scale demo should exercise:

- many tenant partitions;
- explicit repository allowlists;
- bounded first-run ingestion;
- incremental PR sync after first materialization;
- Dagster backfills/materializations across many partitions;
- asset checks and observability over enough tables to be meaningful;
- DuckDB-backed gold metric queries over more than a few rows.

This spec does **not** require 700 customers, cloud deployment, GitHub App auth, Jira/CI/CD ingestion, webhook queues, or production security controls.

## Behavioral Contract

### Small default remains fast

Given a developer runs the project without setting `KABUTO_TENANTS_CONFIG`, the active tenant registry should remain small and fast enough for everyday development.

The default config remains:

```text
config/tenants.example.yaml
```

It should continue to support quick commands such as:

```bash
task materialize TENANT=personal
task materialize TENANT=sandbox
```

### Scale config is opt-in

Given a developer wants portfolio-scale behavior, they should explicitly select:

```bash
export KABUTO_TENANTS_CONFIG=config/tenants.scale.yaml
```

The scale config should contain approximately:

- 20-30 tenant partitions;
- 45-60 repositories total;
- at least 24 distinct repository owners/orgs where practical;
- 1-3 repositories per tenant;
- a mix of open-source stack projects and broader engineering org projects.

Tenant names should be safe, descriptive, and not pretend to be real customers. Prefer names like:

```text
oss_dagster
oss_dlt
oss_duckdb
eng_prometheus
eng_grafana
```

### First-run history is bounded

Given no incremental cursor exists for a tenant/repo, the first scale run should not fetch all historical PRs for large repositories.

The implementation should support an initial history bound, configured by an env var such as:

```bash
export KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180
```

For the scale workflow, docs and task aliases should default to 180 days.

The exact implementation may use GitHub PR `updated_at` ordering and stop pagination once the page's oldest `updated_at` falls before the cutoff. It should preserve existing incremental behavior for later runs.

### Incremental sync remains active after first run

Given a tenant has already materialized once and cursor state exists, later runs should use existing `updated_at` cursors with `KABUTO_GITHUB_INCREMENTAL_LOOKBACK_DAYS` as the safety window.

The scale config should not require full rescans every time.

### Repository curation avoids pathological cases

A repository is eligible for `config/tenants.scale.yaml` if it is:

- public;
- active or recently active enough to produce PR metric rows in the selected window;
- not archived unless intentionally included as a low-activity example;
- not so large that a 180-day first run is likely to exceed practical local demo limits;
- relevant to data engineering, orchestration, API/product engineering, observability, infra, or broadly recognizable engineering tooling.

### Validation does not require full live scale ingestion

Deterministic tests should validate the scale config shape without live GitHub calls:

- YAML loads and validates;
- tenant IDs are unique and path safe;
- repository names are valid `owner/name` strings;
- total repo count is in target range;
- distinct owner count is in target range;
- no token values appear in config.

Live validation should be staged:

1. repo accessibility/rate-limit-safe metadata check for the curated list;
2. materialize a small subset of scale tenants;
3. optionally materialize the full scale config only when the operator explicitly chooses to spend the API/time budget.

## Acceptance Criteria

- `config/tenants.scale.yaml` exists and is opt-in, not the default.
- Scale config contains 20-30 tenants and 45-60 repositories, with at least 24 distinct owners/orgs unless curation evidence explains a small shortfall.
- First-run history can be bounded to 180 days with a documented env var.
- Taskfile/docs teach small default versus opt-in scale workflow.
- Deterministic tests validate scale config shape and first-run lookback behavior without live GitHub calls.
- Live validation evidence, when executed, records which subset/full scale was materialized and the observed row counts/rate-limit posture.

## Constraints

- Do not commit tokens, private GitHub repo names, or secret-bearing env values.
- Keep open-source-first tooling and local-first execution.
- Do not remove the small default workflow.
- Do not claim this represents Jellyfish internals or true production scale; frame it as a portfolio-scale local approximation.
- Avoid GitHub App auth; the user explicitly does not want to create a GitHub App.
