Status: active
Created: 2026-06-19
Updated: 2026-06-19

# GitHub Scale Demo Uses Many Opt-In Tenants

## Context

The project currently demonstrates a production-shaped GitHub ingestion platform with Dagster, dlt, Delta Lake, asset checks, incremental PR sync, REST/MCP exports, and tenant-scoped paths. However, the live configured corpus is too small to justify the tooling in a portfolio review: a few repositories can show correctness, but they do not feel like a serious multi-customer engineering-intelligence data problem.

The user explicitly challenged the mismatch between a Jellyfish-like customer-facing data platform, public references to hundreds of companies, and the current repo count. The goal is not to mimic 700 customers, but to make the local demo credible enough that orchestration, asset checks, incremental sync, observability, tenant partitions, and DuckDB query exports feel warranted.

Clarified user choices:

- Use **many tenants**, not one large tenant.
- Populate the scale demo with a **mix of open-source stack repos and broader engineering org repos**.
- Bound first-run historical scope to **last 180 days**.
- Keep the current small config as the **default**; make scale opt-in.

## Decision

Create an opt-in portfolio-scale GitHub corpus alongside the small default config:

```text
config/tenants.example.yaml   # small/default; fast local dev and tests
config/tenants.scale.yaml     # opt-in scale demo; many tenants and ~50 repos
```

The scale demo should model customer-style isolation by using roughly **20-30 tenant partitions**, with **1-3 repositories per tenant**, totaling roughly **45-60 repositories** across at least **24 owners/orgs** where practical.

The scale demo should use a first-run history bound of **180 days** so an initial materialization does not crawl all historical PRs for large projects.

## Alternatives Considered

### One large `portfolio_scale` tenant with ~50 repos

Rejected because it creates volume but does not exercise tenant partitioning, tenant-scoped observability, customer-style backfills, or isolation in a way that maps to a Jellyfish-like SaaS data platform.

### Replace the small default config with the scale config

Rejected because it would make everyday development too slow and surprising. The small config remains the default; scale runs are explicit.

### Use only Chris's personal/network repos

Rejected for now because it requires more user-provided repo curation and may not naturally reach the desired owner/repo diversity. The selected approach can include personal/friend repos but uses OSS/engineering orgs to create a realistic broader corpus.

### Fetch all history for every repo

Rejected because the initial scale run could be slow, rate-limit heavy, and unnecessary for a portfolio demo. A 180-day window is enough to produce meaningful PR throughput/cycle-time metrics while keeping the demo safe.

## Consequences

- Dagster partitioning becomes visibly useful: 20-30 tenant partitions instead of only a few.
- Incremental sync and initial history bounds become important rather than ornamental.
- The project can demonstrate scale-aware ergonomics: small default, opt-in scale config, bounded initial materialization, staged validation.
- Docs must avoid claiming this is production-scale in an absolute sense; the right claim is **portfolio-scale**, **production-shaped**, and **large enough to make the patterns meaningful locally**.
- Repo selection needs a curation step to avoid pathological repos with enormous PR histories, archived projects, unavailable repos, or repos with no meaningful PR activity.
