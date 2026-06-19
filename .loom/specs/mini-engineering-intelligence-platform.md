Status: draft
Created: 2026-06-18
Updated: 2026-06-18

# Mini Engineering Intelligence Platform

## Purpose and Scope

This spec defines the target behavior for `kabuto-kurage`, a portfolio-quality local learning codebase inspired by Jellyfish's public Staff Data Engineer role requirements and product surface.

The project should demonstrate that Chris can reason about and build the core patterns behind a customer-facing engineering intelligence data platform:

- Third-party developer-tool ingestion.
- Multi-tenant data boundaries.
- Lakehouse storage with Delta Lake.
- Workflow orchestration visible through Dagster UI.
- Engineering productivity / delivery metrics derived from GitHub data.
- Infrastructure-as-code and reproducible local development.
- Operational visibility into pipeline freshness and failures.

This is **not** intended to clone Jellyfish, use Jellyfish private information, or replicate proprietary algorithms. It is a local, open-source-first learning and portfolio project that models public concepts from Jellyfish's product and job posting.

## Primary User

Chris, acting as a Staff Data Engineer candidate and portfolio author.

Secondary readers may include interviewers or collaborators reviewing the repository to understand the architecture, tradeoffs, and execution quality.

## Target Narrative

A reviewer should be able to open the repository and understand this story:

> This project ingests GitHub engineering activity for one or more configured tenants, stores raw and modeled data in Delta Lake, orchestrates batch and near-real-time-style workflows in Dagster, computes tenant-scoped engineering metrics, and exposes enough observability to reason about correctness, freshness, and failures.

## Behavioral Requirements

### Tenant Model

- The system MUST represent at least two tenants, even if both are backed by Chris-controlled GitHub data or test organizations.
- All persisted source records MUST include `tenant_id` or live under an explicitly tenant-scoped storage path.
- All modeled records and metrics MUST preserve tenant identity.
- Any cross-tenant query or metric MUST be explicit; tenant-scoped queries are the default.
- The repository MUST include tests or checks proving that tenant-scoped reads do not include other tenants' data.

### GitHub Ingestion

- The first real source MUST be GitHub's API.
- The initial resource types SHOULD include repositories and pull requests.
- Follow-up resource types MAY include commits, reviews, issues, comments, workflows, or deployments.
- Ingestion MUST handle authentication through local environment variables or ignored secret files.
- Ingestion MUST account for API rate limits and pagination.
- Ingestion MUST persist raw payloads before normalization.
- Ingestion SHOULD track cursors/checkpoints so repeat runs are incremental or at least idempotent.

### Delta Lake Storage

- Delta Lake MUST be introduced early rather than deferred to a late optional phase.
- The storage design SHOULD include bronze/raw, silver/normalized, and gold/metrics layers.
- The project MUST include at least one observable Delta-specific learning artifact, such as documentation or tests inspecting `_delta_log`, table versions, schema evolution, or time travel.
- The implementation SHOULD avoid proprietary/managed dependencies when a viable open-source/local option exists.

### Orchestration

- Dagster UI is the first user-facing surface.
- Core workflows MUST be represented as Dagster assets or jobs.
- The Dagster asset graph SHOULD make the movement from GitHub raw data to metrics visible.
- The project SHOULD use partitions where they clarify tenant/date/source processing.
- At least one scheduled/reconciliation workflow SHOULD exist.
- A later near-real-time path MAY use a sensor or event table/queue, but should not block the first coherent demo.

### Metrics

The first metric layer SHOULD include a subset of:

- Pull request throughput over time.
- Pull request cycle time.
- Review latency.
- Time from PR open to merge.
- Unlinked pull requests, if issue-linking is modeled.
- Repository/team contribution summaries.

Metrics MUST be tenant-scoped.

### Observability

The project SHOULD expose or document:

- Last successful ingestion by tenant/source/resource.
- Freshness/lag indicators.
- Failed runs and retry behavior.
- GitHub API rate-limit status where available.
- Dagster run status and asset materialization history.

### Infrastructure and Local Development

- The project MUST be reproducible locally.
- Infrastructure-as-code MUST be represented with Terraform where practical.
- Docker Compose MAY be used for local services and developer ergonomics.
- Secrets MUST not be committed.
- Setup instructions MUST explain the minimum path to run the Dagster UI and materialize the first assets.

## Non-Goals for the Initial Plan

- Building a polished customer web application.
- Building a full clone of Jellyfish's API or UI.
- Supporting all developer-tool integrations.
- Supporting enterprise auth, billing, or production-grade security.
- Using proprietary managed platforms where local open-source substitutes are viable.
- Optimizing for cloud deployment before the local portfolio story is coherent.

## Acceptance Criteria

A first major milestone is acceptable when:

1. A reviewer can follow README instructions to start the local environment and open Dagster UI.
2. At least one GitHub-backed tenant can be ingested through a Dagster workflow.
3. Raw GitHub payloads are persisted in Delta Lake.
4. Normalized PR/repository tables are derived from raw data.
5. At least two tenant-scoped metrics are computed and visible through Dagster materializations or documented query outputs.
6. Tenant boundary tests or validation queries exist.
7. The repository includes architecture notes explaining how the local system maps to Jellyfish-relevant concepts: IaC, orchestration, lakehouse, multi-tenancy, ingestion, and observability.

## Related Records

- `.loom/research/2026-06-18-jellyfish-company-research.md`
- `.loom/research/2026-06-18-jellyfish-interview-walk-notes.md`
- `.loom/knowledge/project-purpose.md`
