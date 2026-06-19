Status: done
Created: 2026-06-18
Updated: 2026-06-18

# Jellyfish Company Research for Local Learning Project

## Question

Before creating Loom implementation plans for this repository, what can we verify about Jellyfish, the engineering insights / software engineering intelligence company, and what should that imply for a local learning codebase?

## Sources and Methods

Research performed via web search and fetched public pages on 2026-06-18.

Primary/public sources consulted:

- Jellyfish Staff Data Engineer posting on Built In: https://builtin.com/job/staff-data-engineer/9719422
- Jellyfish integrations page: https://jellyfish.co/integrations/
- GitHub integration page: https://jellyfish.co/integration/github/
- Jira integration page: https://jellyfish.co/integration/jira/
- Data Hub product page: https://jellyfish.co/platform/data-hub/
- Data Hub launch blog: https://jellyfish.co/blog/introducing-jellyfish-data-hub-flexible-curated-engineering-insights/
- New integrations blog: https://jellyfish.co/blog/new-data-integrations/
- Jellyfish API + Grafana blog: https://jellyfish.co/blog/integrating-jellyfish-insights-with-grafana/
- Jellyfish AI Engineering Trends newsroom post: https://jellyfish.co/newsroom/jellyfish-reveals-ais-real-impact-on-engineering-teams/
- Jellyfish MCP GitHub repository: https://github.com/Jellyfish-AI/jellyfish-mcp
- Docker Hub / MCP search snippets for Jellyfish MCP: https://hub.docker.com/r/jellyfishco/jellyfish-mcp

Reliability notes:

- Job posting requirements are highly relevant because they explicitly describe the role's expected work.
- Product pages and blogs are reliable for what Jellyfish publicly claims its product does, but not for hidden implementation details.
- Public MCP repository is reliable evidence of public API categories and some technology choices for that MCP package, not necessarily their internal platform stack.
- No public source found that directly confirms their internal orchestrator, warehouse/lake engine, queue, cloud provider, or exact tenancy model.

## Executive Summary

The Staff Data Engineer role is not generic internal analytics. Public evidence points to a product data-platform role around integrations, cloud data infrastructure, workflow orchestration, exports, and tooling.

The strongest verified signals:

1. The job posting explicitly says the role owns scalable data pipelines, integrations, cloud data infrastructure, IaC with Terraform, near-real-time and batch workflow orchestration, third-party API integrations, AI/LLM integrations, data export pipelines, and internal tooling.
2. Delta Lake / lakehouse architecture is a bonus qualification, not listed as mandatory.
3. Jellyfish's product integrates engineering-system data such as GitHub repos/PRs/issues and Jira epics/issues/statuses.
4. Product materials repeatedly emphasize unifying fragmented SDLC data into a single engineering data model / insight layer.
5. Jellyfish exposes customer-accessible analytics data through an API with domains including allocations, delivery, metrics, people, teams, AI impact, and DevEx.
6. Jellyfish has an open-source MIT-licensed MCP server, implemented in Node.js, wrapping Jellyfish API export endpoints for AI-agent access.

Implication for this repo:

> Build a local, open-source, mini engineering-intelligence platform that models multi-tenant developer-tool ingestion, batch + near-real-time orchestration, tenant-scoped storage/transforms, export APIs, and product-like metrics.

## Findings

### 1. Role Requirements: Staff Data Engineer

The Staff Data Engineer posting is the most important source for project design.

Verified responsibilities from the posting:

- Define architecture and long-term technical direction for data pipelines and integrations platform.
- Design and implement storage, transformation, and export at scale.
- Drive integrations with third-party tools and standards for future integrations.
- Own infrastructure-as-code strategy using Terraform.
- Evolve cloud data infrastructure.
- Architect workflow orchestration systems for near-real-time and batch data processing.
- Lead data export pipelines for diverse customer needs.
- Build internal tooling and agentic workflows.
- Lead design reviews, mentor engineers, and communicate tradeoffs.

Verified qualifications / preferences:

- Expert Python engineer.
- Deep experience scaling data pipelines and owning complex data infrastructure end-to-end.
- Large-scale third-party API integration experience.
- IaC fluency: Terraform, CloudFormation, or similar.
- Workflow orchestration production experience: Prefect, Airflow, or Dagster.
- AI/LLM tool integration experience.
- Bonus: Delta Lake and lakehouse architectures.
- Bonus: deep integrations with developer tools such as Jira, GitHub, GitLab, and CI/CD systems.

Interpretation:

- Terraform is not speculative; it is explicitly named.
- Dagster is plausible but not specifically required; posting names Prefect, Airflow, or Dagster as examples.
- Delta Lake is plausible but not confirmed as in use; posting calls Delta/lakehouse a bonus.
- Near-real-time + batch is explicit, so a local project should include both schedule/reconciliation and event/sensor/queue-ish paths.

### 2. Product Surface: Engineering Intelligence / Data Hub

Jellyfish's Data Hub and platform pages frame the product as an engineering intelligence layer, not just dashboards.

Verified product claims:

- Data Hub is described as a launchpad for engineering intelligence that connects signals across engineering systems.
- It combines AI impact, DORA metrics, and flexible custom metrics/dashboards.
- It emphasizes flexible, transparent logic for standardizing metrics while allowing team-level nuance.
- It supports custom metrics and dashboards.
- It presents Jira tickets, PR data, and AI usage together in one view.
- It offers AI-assisted custom queries.
- Launch blog says Data Hub enriches raw system data into a high-fidelity map of the engineering organization.
- Launch blog emphasizes cross-system synthesis across tools like SonarQube, GitHub, and AI agents.
- Human-centric metadata includes tagging, team structures, and proprietary Jellyfish insights such as Person-Weeks.

Interpretation:

A good local learning project should not stop at raw ingestion. It should include:

- Engineering-domain entities: people, teams, repos, PRs, issues, incidents/builds.
- A normalized semantic layer / modeled tables.
- Derived product metrics: cycle time, PR throughput, review latency, DORA-ish measures, allocations/work categories.
- A small export/query interface to make the metrics feel product-facing.

### 3. Integrations: GitHub, Jira, CI/CD, Incidents, Monitoring, AI Tools

Verified integration details:

- GitHub integration syncs repos, PRs, and issues to map work and measure cycle time.
- GitHub integration supports direct connection or Jellyfish Agent.
- GitHub data powers delivery visibility, workflows across Metrics / Life Cycle Explorer / Deliverables / Team Summaries, allocation/work mapping, operational reporting, DevOps lead time metrics, and delivery performance insights.
- Jira integration syncs epics, issues, and statuses to track delivery and investment allocation.
- Jira supports Cloud and Data Center via direct connection or Jellyfish Agent.
- Jira captures metadata about assigned ticket movements and ticket management events, including custom fields.
- New integrations blog claims 25+ new integrations across Incident Management, Security, CI/CD, QA, ITSM, Error Tracking, Monitoring, and Customer Support.
- That same blog says integrations offer real-time data streaming and self-service setup.

Interpretation:

A realistic learning project should model integration variability:

- Different source systems have different resource types and schemas.
- Some sources can be polled; some emit events/webhooks.
- Enterprise/self-hosted integrations may require an agent-like pattern.
- Custom fields and schema variability matter, especially Jira.

Local implementation analogue:

- Mock GitHub resources: repos, PRs, commits, reviews, issues.
- Mock Jira resources: epics, issues, status transitions, custom fields.
- Optional CI/CD resources: builds/deployments, failures, durations.
- Optional incident resources: incidents, severity, MTTR.
- Store raw source payloads before normalization.

### 4. API / Export Surface

Jellyfish publishes an API used for external reporting and integrations.

Verified from Grafana blog:

- The Jellyfish API gives access to three core domains: Deliverables, Allocations, and Metrics.
- The blog demonstrates Grafana consuming a Jellyfish API endpoint using an API token.
- Example endpoint: `https://app.jellyfish.co/endpoints/export/v0/delivery/work_category_contents?...`
- Authentication example uses `Authorization: Token [your Jellyfish API token]`.

Verified from Jellyfish MCP repository:

- Public MCP server wraps Jellyfish API endpoints.
- The MCP server uses `JELLYFISH_API_TOKEN` and `JELLYFISH_API_BASE_URL`, defaulting to `https://app.jellyfish.co`.
- It fetches API schema from `/endpoints/export/v0/schema`.
- It forces `format=json` on API requests.
- Tool/API categories include:
  - AI Impact: company/team/person adoption and impact analytics.
  - Allocations: by person, team, investment category, work category, summaries, filters.
  - Delivery: deliverable scope/effort history, work categories, deliverable search/details.
  - DevEx: insights by team.
  - Metrics: company/person/team metrics, team sprint summary, unlinked pull requests.
  - People: list/search engineers.
  - Teams: list/search teams.
  - Help Center: search/get articles.
- MCP repository package details:
  - Package name: `jellyfish-mcp-server`.
  - MIT license.
  - Node.js ESM package.
  - Dependencies include `@modelcontextprotocol/sdk`, `@toon-format/toon`, and `js-yaml`.
  - Docker support exists.

Interpretation:

A local project should include an API/export layer, because exports are explicit in the job and public product:

- `/api/v1/metrics/company`
- `/api/v1/metrics/team`
- `/api/v1/allocations/by-team`
- `/api/v1/delivery/work-categories`
- `/api/v1/delivery/deliverables`
- Potential future MCP wrapper, because Jellyfish publicly uses MCP for AI access to engineering metrics.

### 5. Scale / Market Traction Claims

Verified public claims:

- 2026 newsroom post says AI Engineering Trends is based on more than 700 companies, 200,000 engineers, and 20 million PRs.
- Same newsroom post's About section says Jellyfish helps 500+ companies including DraftKings, Keller Williams, and Blue Yonder.
- Another fetched snippet from a 2026 blog claimed a regularly updated study based on more than 1,000 companies, 200,000 engineers, and 37 million PRs.

Interpretation and caution:

- These are company-reported numbers and should be treated as marketing/product claims.
- Still, they imply a product/data platform whose hard problems include high-cardinality tenants, many engineers, many PRs/issues/events, and evolving source-system integrations.

### 6. Multi-Tenancy Is Implied, Not Publicly Detailed

No public source found describing Jellyfish's internal tenancy model.

However, multi-tenancy is strongly implied by:

- Serving 500+ companies.
- Integrating with each customer's engineering tools.
- Product pages describing customer-specific engineering insights.
- API access to organization-specific engineering metrics.

What is not verified:

- Whether tenant isolation is database-per-tenant, schema-per-tenant, shared tables with tenant IDs, storage-prefix isolation, row-level security, or some hybrid.
- Whether Terraform provisions tenant-specific resources.
- Whether Delta Lake partitioning uses tenant/date/source/resource or another model.

Local project implication:

- Implement explicit `tenant_id` everywhere.
- Add tests that tenant-scoped queries cannot leak data.
- Model tenant configuration as code.
- Keep architecture flexible enough to discuss alternative isolation patterns.

### 7. Near-Real-Time + Batch Is Confirmed at Requirement Level

The job posting explicitly says workflow orchestration systems for near-real-time and batch data processing.

The integrations blog says integrations offer real-time data streaming.

Interpretation:

For a local project, include both:

- Batch reconciliation jobs: scheduled API polling / fixture polling.
- Near-real-time path: webhook/event ingestion into a durable queue or event log, consumed by orchestrated jobs.

Open-source local options:

- Redis Streams, NATS JetStream, RabbitMQ, Redpanda/Kafka-compatible, or just Postgres-backed event table for first slice.
- Dagster sensors can simulate near-real-time orchestration while schedules handle reconciliation.

### 8. Lakehouse / Delta Lake Is Relevant but Not Confirmed

The job posting lists Delta Lake and lakehouse architectures as bonus points.

That means:

- Worth learning.
- Useful to include in the project if feasible.
- But do not claim Jellyfish uses Delta Lake unless a stronger source is found.

Local project options:

- Use Delta Lake locally if setup is not too heavy.
- Or begin with Parquet + DuckDB and explicitly document what Delta/Iceberg adds: transaction log, snapshots, schema evolution, time travel, deletes/updates, compaction semantics.
- If using Delta, include an exercise that inspects `_delta_log/`.

### 9. AI/LLM Infrastructure Is Now Part of the Product Story

The Staff Data Engineer posting explicitly asks for AI/LLM tool integrations and agentic workflows.

Public product materials emphasize:

- AI impact analytics.
- AI adoption and impact metrics.
- AI-assisted custom queries.
- Jellyfish Assistant.
- Jellyfish MCP.
- Integrations with tools like GitHub Copilot, Cursor, Claude Code, Augment Code, Amazon Q Developer, etc.

Local project implication:

- The core learning project can remain data-platform-first.
- A later phase could expose metrics via a local MCP server or agent-friendly API.
- Model AI coding tool events as another source type if time allows.

## What We Should Build Toward

### Project Thesis

Build a local, open-source, miniature version of the kind of platform a Jellyfish Staff Data Engineer might help design:

> A multi-tenant engineering-intelligence data platform that ingests developer-tool signals, orchestrates batch and near-real-time pipelines, stores raw and modeled data, computes tenant-scoped engineering metrics, exposes exports/APIs, and includes infrastructure-as-code and observability.

### Capabilities to Represent

1. **Tenant management**
   - Tenants as configuration/code.
   - Tenant-specific source credentials represented with fake/local secrets.
   - Every dataset and API response is tenant-scoped.

2. **Third-party integrations**
   - Mock GitHub and Jira initially.
   - Optional CI/CD and incident sources later.
   - Source-specific raw payloads and normalized models.

3. **Ingestion patterns**
   - Batch polling with cursors.
   - Near-real-time webhook/event path.
   - Idempotent writes and retries.

4. **Orchestration**
   - Dagster assets/jobs/schedules/sensors/partitions, or a comparable orchestrator.
   - Backfill story for tenant/date/source partitions.

5. **Storage and transformations**
   - Bronze/raw, silver/normalized, gold/metrics layers.
   - Start with DuckDB/Parquet if needed; upgrade to Delta/Iceberg for lakehouse practice.
   - Schema evolution exercise.

6. **Metrics/product layer**
   - PR throughput.
   - PR cycle time.
   - Review latency.
   - Unlinked PRs.
   - Jira issue cycle time.
   - Work allocation by category/team/person.
   - DORA-ish deployment frequency/lead time if CI/CD source is added.

7. **Export/API layer**
   - Customer-facing metric endpoints modeled after public Jellyfish API categories.
   - Tenant-scoped auth placeholder.
   - Optional Grafana dashboard or MCP wrapper later.

8. **IaC / local infrastructure**
   - Terraform for local resources where practical.
   - Docker Compose for services.
   - Optional MinIO for S3-compatible object storage.
   - Queue service for events.
   - Observability services.

9. **Observability**
   - Run status by tenant/source.
   - Freshness/lag by tenant/source.
   - API rate-limit simulation.
   - Queue depth or event backlog.
   - Error/retry counts.

## Recommended Scope for Loom Plans

Do not try to build the whole thing in one plan. Use a parent plan with child tickets, roughly:

1. Project scaffold and local developer environment.
2. Tenant and source configuration model.
3. Mock GitHub/Jira data generator or fixture source.
4. Batch ingestion into raw storage.
5. Modeled transformations and metrics in DuckDB/Parquet.
6. Dagster orchestration with schedules and partitions.
7. Near-real-time webhook/event queue + Dagster sensor.
8. Tenant-scoped API/export service.
9. IaC with Terraform/Docker Compose.
10. Observability and SLA dashboard.
11. Optional lakehouse upgrade: Delta/Iceberg + schema evolution lab.
12. Optional MCP/export agent integration.

## Open Questions Before Planning

Need user decisions before converting this into executable Loom tickets:

1. Should the first implementation optimize for interview readiness within days, or a deeper learning platform over weeks?
2. Should the storage path start simple with DuckDB/Parquet, or force Delta/Iceberg early?
3. Should Dagster be the orchestrator from day one, or introduced after a simple pipeline exists?
4. How much UI/API should exist initially: CLI only, REST API, dashboard, or MCP?
5. Should we use real GitHub API data from Chris's account/repos, or fully synthetic fixtures first?

## Related Records

- `.loom/knowledge/project-purpose.md`
- `.loom/research/2026-06-18-jellyfish-interview-walk-notes.md`
