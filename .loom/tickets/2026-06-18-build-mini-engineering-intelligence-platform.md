Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: none
Depends-On: .loom/specs/mini-engineering-intelligence-platform.md, .loom/decisions/initial-portfolio-architecture.md

# Build Mini Engineering Intelligence Platform

## Scope

Parent orchestration plan for building `kabuto-kurage` into a portfolio-quality local mini engineering intelligence data platform inspired by Jellyfish-relevant Staff Data Engineer responsibilities.

This parent ticket is not directly executable. It coordinates the child tickets that should be executed in sequence or in small parallel batches.

The project should demonstrate:

- GitHub API ingestion for tenant-scoped engineering data.
- Delta Lake bronze/silver/gold storage.
- Dagster UI as the first user-facing surface.
- Multi-tenant boundaries and validation.
- Infrastructure-as-code and reproducible local setup.
- Operational visibility and portfolio documentation.

## Out of Scope

- Production cloud deployment.
- Cloning Jellyfish's proprietary product.
- Supporting every developer-tool integration.
- Building a polished customer web app before the data platform works.

## Child Tickets

### Phase 1: Foundation and Technical Validation

1. `.loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md`
   - Decide exact Python/Delta/Dagster/GitHub libraries and prove they can work together locally.

2. `.loom/tickets/2026-06-18-scaffold-portfolio-data-platform.md`
   - Create repository structure, Python tooling, tests, linting, docs skeleton, and local environment conventions.

3. `.loom/tickets/2026-06-18-model-tenants-and-source-config.md`
   - Define tenant/source configuration, secret conventions, and tenant boundary rules.

### Phase 2: Ingestion and Lakehouse Core

4. `.loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md`
   - Ingest GitHub repositories and pull requests into raw/bronze Delta tables.

5. `.loom/tickets/2026-06-18-build-silver-github-models.md`
   - Normalize raw GitHub payloads into stable silver tables.

6. `.loom/tickets/2026-06-18-add-dagster-asset-graph.md`
   - Represent ingestion and transformations as Dagster assets visible in Dagster UI.

### Phase 3: Metrics, Correctness, and Operations

7. `.loom/tickets/2026-06-18-build-gold-engineering-metrics.md`
   - Compute tenant-scoped PR throughput, cycle time, and review-related metrics.

8. `.loom/tickets/2026-06-18-validate-tenant-isolation.md`
   - Add automated validation that tenant-scoped reads and metrics do not leak data.

9. `.loom/tickets/2026-06-18-add-observability-and-freshness.md`
   - Track freshness, failures, rate limits, and run status in a visible way.

### Phase 4: Portfolio Polish and Jellyfish-Relevant Extensions

10. `.loom/tickets/2026-06-18-add-local-iac.md`
    - Add Terraform/Docker Compose-backed local infrastructure definition.

11. `.loom/tickets/2026-06-18-write-portfolio-architecture-docs.md`
    - Produce README, architecture diagrams, and interview-facing explanation.

12. `.loom/tickets/2026-06-18-plan-export-api-followup.md`
    - Shape the next milestone for Jellyfish-like export APIs or MCP after Dagster-centered MVP.

## Sequencing

Recommended execution order:

1. Execute child 1 first; it resolves the highest-risk technical choices.
2. Execute children 2 and 3 after child 1.
3. Execute child 4, then child 5.
4. Execute child 6 once the core data flow exists.
5. Execute children 7 and 8 together or sequentially; tenant isolation should be validated before portfolio claims are made.
6. Execute child 9 after metrics exist.
7. Execute children 10 and 11 near the end of the first milestone.
8. Execute child 12 only after the Dagster-centered MVP is coherent.

## Acceptance Criteria

The parent plan can move to done when:

- All required child tickets through child 11 are done or explicitly superseded by better-scoped tickets.
- The spec acceptance criteria in `.loom/specs/mini-engineering-intelligence-platform.md` are satisfied.
- There is evidence showing a fresh local run through Dagster UI from GitHub ingestion to metrics.
- There is evidence showing tenant isolation validation.
- README and architecture docs explain how the project maps to Jellyfish-relevant concepts.

## Current State

Done. The Dagster-centered mini engineering intelligence platform MVP is implemented and validated.

Completed child tickets:

- `.loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md`
- `.loom/tickets/2026-06-18-scaffold-portfolio-data-platform.md`
- `.loom/tickets/2026-06-18-model-tenants-and-source-config.md`
- `.loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md`
- `.loom/tickets/2026-06-18-build-silver-github-models.md`
- `.loom/tickets/2026-06-18-add-dagster-asset-graph.md`
- `.loom/tickets/2026-06-18-build-gold-engineering-metrics.md`
- `.loom/tickets/2026-06-18-validate-tenant-isolation.md`
- `.loom/tickets/2026-06-18-add-observability-and-freshness.md`
- `.loom/tickets/2026-06-18-add-local-iac.md`
- `.loom/tickets/2026-06-18-write-portfolio-architecture-docs.md`
- `.loom/tickets/2026-06-18-plan-export-api-followup.md`

Final evidence: `.loom/evidence/2026-06-18-final-mvp-validation.md`.

The export/API follow-up was shaped as `.loom/tickets/2026-06-18-build-engineering-metrics-export-surface.md` and is intentionally blocked pending a product/operator decision to begin that new milestone.

## Journal

- 2026-06-18: Parent plan created from user-approved direction: portfolio project, Delta Lake early, GitHub API first, Dagster UI first.
- 2026-06-18: Drained runnable child tickets in dependency order.
- 2026-06-18: Recorded final validation evidence covering tests, lint, type checks, Terraform validation, and bounded live Dagster CLI materialization from GitHub ingestion through gold metrics.
- 2026-06-18: Moved parent plan to done.

## Progress and Notes

- 2026-06-18: Parent plan created from user-approved direction: portfolio project, Delta Lake early, GitHub API first, Dagster UI first.
- 2026-06-18: Implemented MVP across stack validation, scaffold, tenancy, GitHub bronze, silver, Dagster assets, gold metrics, tenant isolation, observability, local IaC, and portfolio docs.

## Blockers

None for the Dagster-centered MVP. Follow-up export/API implementation is blocked pending explicit selection of the new milestone.
