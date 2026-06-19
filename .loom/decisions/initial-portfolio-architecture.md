Status: active
Created: 2026-06-18
Updated: 2026-06-18

# Initial Portfolio Architecture

## Context

Chris asked to shape a new learning codebase before implementation. The project is meant to prepare for and demonstrate relevance to Jellyfish's Staff Data Engineer role.

Prior research found that the public Staff Data Engineer posting explicitly emphasizes:

- Scalable data pipelines and integrations.
- Infrastructure as code, especially Terraform.
- Workflow orchestration for near-real-time and batch data processing.
- Third-party API and AI/LLM integrations.
- Data export pipelines.
- Bonus experience with Delta Lake and lakehouse architectures.

Chris answered planning questions with these preferences:

- Optimize for a **portfolio project**, not only a quick interview cram demo.
- Use **Delta Lake early**.
- Use **Chris's GitHub API** data for the first ingestion pipeline.
- Make **Dagster UI** the first user-facing surface.

The project also inherits the open-source-first principle from repository-level instructions.

## Decision

Build `kabuto-kurage` as a local, open-source-first, portfolio-quality mini engineering intelligence platform with this initial architecture:

1. **Python-first data platform** for ingestion, transformations, tests, and Dagster orchestration.
2. **GitHub API as the first real integration**, beginning with repositories and pull requests.
3. **Delta Lake as the early storage layer**, with bronze/raw, silver/normalized, and gold/metrics tables.
4. **Dagster UI as the first visible product surface**, showing assets, runs, partitions, materializations, and freshness.
5. **Explicit multi-tenancy from the start**, with tenant configuration and tenant-scoped persisted data.
6. **Terraform included early enough to demonstrate IaC**, but not allowed to block the first Dagster + Delta + GitHub learning loop.
7. **REST/API/MCP/dashboard surfaces deferred until after the Dagster-centered data platform is coherent.**

## Alternatives Considered

### 3-day interview prep demo

Rejected because Chris selected portfolio project. A short demo might optimize for speed but would undercut deeper learning and public-code quality.

### DuckDB/Parquet first

Rejected for the initial direction because Chris selected Delta Lake early. DuckDB may still be useful for local querying, but the storage learning target is Delta Lake.

### Synthetic fixtures first

Rejected as the primary first pipeline because Chris selected GitHub API. Synthetic fixtures may still be used for tests and deterministic edge cases.

### REST API or dashboard as first surface

Rejected for initial surface because Chris selected Dagster UI. Export APIs and dashboards remain relevant later because Jellyfish publicly exposes API/export surfaces.

## Consequences

Positive consequences:

- The project maps directly to the job posting's major themes.
- Dagster UI provides immediate visual evidence of orchestration and asset thinking.
- Real GitHub data forces handling of pagination, rate limits, schemas, authentication, and incremental ingestion.
- Delta Lake early creates concrete learning around transaction logs, schema evolution, and lakehouse table behavior.
- Portfolio orientation justifies stronger docs, diagrams, tests, and architecture notes.

Tradeoffs and risks:

- Delta Lake setup may add complexity compared with Parquet/DuckDB.
- Real GitHub API data can introduce non-determinism and rate-limit issues.
- Terraform may feel artificial for local-only resources unless scoped carefully.
- Dagster-first development can slow simple pipeline iteration if over-modeled too early.
- A portfolio-quality repo requires more documentation and polish than a private learning sandbox.

Risk mitigations:

- Use synthetic fixtures for tests even while real GitHub API powers the demo path.
- Start with a minimal GitHub resource set: repos and pull requests.
- Keep Terraform focused on reproducibility and local services rather than pretending to manage production cloud resources.
- Create a dedicated early ticket to validate the Delta Lake library/runtime choice before deeper implementation.

## Related Records

- `.loom/specs/mini-engineering-intelligence-platform.md`
- `.loom/research/2026-06-18-jellyfish-company-research.md`
- `.loom/knowledge/project-purpose.md`
