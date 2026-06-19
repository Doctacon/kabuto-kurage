Status: active
Created: 2026-06-18
Updated: 2026-06-18

# Jellyfish Interview Walk Notes: IaC, Multi-Tenancy, Orchestration, and Lakehouse Concepts

## Question

Chris had a long voice conversation with an LLM while walking and wants the ideas converted into a durable Markdown reference for this new learning codebase.

The conversation centered on preparing for a possible Staff Data Engineer interview at Jellyfish, especially around gaps between Chris's current internal-analytics background and a customer-facing product data platform.

## Source and Reliability

Source: pasted transcript from a walk conversation with an LLM on 2026-06-18.

Reliability notes:

- This is **not verified research**.
- Statements about Jellyfish's stack, customer count, ARR, Delta Lake usage, and internal architecture are assumptions or recruiter-conversation recollections unless separately sourced.
- Treat this record as a map of concepts to learn and questions to verify, not as evidence of what Jellyfish actually runs.

## Core Framing

Chris's current data engineering context at Harness is mostly internal analytics:

- SQLMesh handles SQL transformation workflows.
- A post-hook applies permissions from YAML after runs.
- Pipelines run mostly in Harness CI on cron schedules.
- Monitoring/alerting exists through Slack and custom SLA dashboards in Metabase.
- Stakeholders are internal consumers.

The suspected Jellyfish context is different:

- Jellyfish's product appears to be engineering intelligence / analytics sold to external customers.
- Data engineering may directly power the customer-facing product, not just internal reporting.
- Customer data likely comes from integrations such as Jira, GitHub, CI/CD systems, and possibly other engineering workflow tools.
- This implies multi-tenant ingestion, transformation, storage, permissions, observability, and serving concerns.

Key mental shift:

> Internal analytics DE optimizes for trusted internal stakeholders. Product data-platform DE optimizes for correctness, isolation, reliability, and user-facing guarantees across many external tenants.

## Major Topics From the Conversation

### 1. Infrastructure as Code

The conversation framed Infrastructure as Code as defining infrastructure resources declaratively and version-controllably, rather than manually configuring environments.

Likely tools and concepts to understand:

- Terraform: common declarative IaC tool.
- Pulumi: IaC using general-purpose languages such as TypeScript, Python, or Go.
- Docker Compose: local container infrastructure as code.
- Kubernetes YAML manifests: declarative workloads, services, config, secrets, etc.
- K3s / Minikube / kind: local Kubernetes learning environments.

Important interview framing:

- Chris can connect existing experience to IaC by emphasizing automation, reproducibility, and declarative permissioning.
- But classic IaC usually means broader resources: compute, storage, networks, databases, identity, service accounts, queues, and deployment environments.
- A local Terraform project can still teach core concepts: resources, modules, state, variables, outputs, plans, and applies.

Potential local practice:

- Terraform manages Docker containers and networks locally.
- Terraform writes local config files using the `local` provider.
- Docker Compose defines Postgres/DuckDB-compatible services, MinIO, Dagster, and observability services.
- Optional: K3s/kind cluster with Kubernetes manifests for local deployment practice.

### 2. Why Dagster Instead of CI Cron Jobs?

Chris currently runs data pipelines through CI cron schedules with Slack alerting and external SLA dashboards. The conversation explored when a team would evolve toward Dagster.

Possible reasons a team adopts Dagster:

- Pipeline dependencies become too complex for independent cron jobs.
- Teams need asset-level lineage: what dataset was produced, from which upstream inputs, and what depends on it.
- Backfills and reprocessing need to be controlled and observable.
- Event-driven or hybrid scheduling becomes useful.
- Data quality checks and metadata become part of the orchestration model.
- Business-critical customer-facing data products need a unified control plane for runs, retries, alerts, and status.

Dagster concepts to learn:

- Assets: data products / datasets as first-class objects.
- Jobs: executable selections of assets or operations.
- Schedules: time-based runs.
- Sensors: event- or condition-based triggers.
- Partitions: time- or tenant-scoped materialization units.
- Backfills: re-materializing historical partitions.
- Observability: run history, logs, asset status, lineage.

Interview narrative:

> My current system uses CI as a practical scheduler, which works well while dependencies are simple. I understand why a product data platform might move to Dagster once asset dependencies, tenant-specific runs, backfills, observability, and customer-facing reliability become central.

### 3. Multi-Tenant Data Architecture

The conversation kept returning to tenant isolation: if Jellyfish ingests Jira/GitHub data for many customers, how is each customer kept separate?

Common tenant-isolation options:

1. Database per tenant
   - Strong isolation.
   - Easier customer-specific backup/restore and deletion.
   - Higher operational overhead.

2. Schema per tenant
   - Moderate isolation.
   - Easier to manage than database-per-tenant.
   - Can become difficult with many tenants and migrations.

3. Shared tables with `tenant_id`
   - Efficient and common at scale.
   - Requires rigorous query scoping and access controls.
   - Often paired with row-level security, application-level authorization, and automated tests.

4. Storage-prefix or table-partition isolation
   - Common in lakehouse/object-store designs.
   - Example: tenant-scoped paths or partitions.
   - Requires careful metadata, permissions, compaction, and query design.

Best-practice themes:

- Every record must carry tenant identity or live in a tenant-specific boundary.
- Every pipeline run must be scoped to a tenant, tenant batch, or explicitly all tenants.
- Every query path must enforce tenant filtering or authorization.
- Access control should be automated, tested, and reviewed.
- Encryption in transit and at rest is table stakes.
- Resource quotas or workload isolation prevent noisy-neighbor problems.
- Auditing and observability should include tenant context.

Open questions for Jellyfish:

- Is customer data isolated by database, schema, table partition, storage prefix, or another model?
- Do they use row-level security anywhere?
- How do they prevent cross-tenant data leakage in transformations and serving layers?
- Are tenant resources provisioned individually through IaC?
- How do they handle tenant deletion/export/compliance requirements?

### 4. Large-Scale Ingestion: Batch, Events, Queues, and APIs

The conversation explored how a company might ingest data from many customers' GitHub/Jira/CI systems.

Possible ingestion modes:

1. Scheduled batch polling
   - Periodically call APIs for each tenant/source.
   - Use cursors, timestamps, or incremental IDs.
   - Simpler to reason about.
   - Can be expensive or stale if intervals are too frequent/infrequent.

2. Webhooks into a durable queue
   - Source systems send events to an endpoint.
   - Endpoint validates and writes events to a broker/queue.
   - Workers or orchestrators consume events in batches.
   - Better freshness but more operational complexity.

3. Hybrid
   - Webhooks for freshness.
   - Periodic reconciliation/backfill jobs to catch missed events.
   - Common for correctness-sensitive systems.

Streaming vocabulary from the conversation:

- Producer: system that emits events, e.g. GitHub webhook sender.
- Broker / queue: durable buffer, e.g. Kafka, RabbitMQ, SQS-compatible service, Redis Streams, NATS JetStream.
- Consumer: worker or orchestrator process that reads events and acts on them.
- Dead-letter queue: place for repeatedly failing messages.

Water-line analogy:

- City/source produces water = producer emits events.
- Water main/pipes = broker/queue carries and buffers events.
- Household = consumer receives events when it is ready.

Failure-handling patterns:

- Acknowledge messages only after successful processing.
- Retry transient failures with backoff.
- Send poison messages to a dead-letter queue.
- Make ingestion idempotent to tolerate duplicate delivery.
- Track cursors/checkpoints per tenant/source/resource.
- Alert on lag, error rates, and stale tenants.

Important nuance:

Event-driven does not necessarily mean running a full data pipeline for every commit. Events can be buffered and processed by count thresholds, time windows, tenant/source grouping, or downstream SLA needs.

Potential local practice:

- Mock GitHub events with a script or small HTTP webhook receiver.
- Write events to Redis Streams, RabbitMQ, or a local Kafka-compatible broker.
- Use a Dagster sensor to trigger a tenant/source ingestion job when enough events accumulate.
- Add a scheduled reconciliation job to demonstrate hybrid ingestion.

### 5. Delta Lake / Iceberg / Lakehouse Concepts

The conversation discussed Delta Lake and Apache Iceberg as lakehouse table formats.

High-level model:

- Data files are usually Parquet files in object storage or a filesystem.
- Metadata tracks tables, files, schemas, snapshots/versions, and operations.
- These formats add ACID-like guarantees, schema evolution, time travel, and more reliable table management on top of files.

Delta Lake specifics to learn:

- Delta tables store Parquet data files plus a `_delta_log/` transaction log.
- The transaction log is an ordered history of JSON commit files and checkpoint files.
- Log entries record actions such as adding/removing files, metadata changes, protocol versions, and schema updates.
- Old Parquet files remain as written; new writes may use newer schemas.
- Readers use the transaction log to determine the active set of files and table schema for a version.
- Time travel is possible because older table versions can be reconstructed from the log, subject to retention/vacuum.

Iceberg contrast to verify later:

- Iceberg uses metadata files, manifests, manifest lists, snapshots, and a catalog pointer model rather than Delta's `_delta_log` design.
- Both solve similar problems but differ in internals and ecosystem fit.

DuckDB nuance:

- DuckDB can query Parquet files and object stores directly.
- To correctly read Delta tables as Delta tables, verify current DuckDB Delta support/extensions rather than assuming raw Parquet reads are equivalent. Reading raw Parquet can ignore deletes, updates, and transaction-log state.

Potential local practice:

- Create a local Delta table for GitHub commits.
- Write version 1 records with a simple schema.
- Simulate API schema changes by adding columns or changing nested JSON handling.
- Inspect data files and `_delta_log/` JSON files.
- Query current and historical versions.
- Compare with querying raw Parquet to understand what the log adds.

### 6. Partitioning and Schema Evolution for GitHub-Like Data

A possible table shape discussed:

- Raw/bronze table: append-only API payloads by tenant, source, resource, ingestion time, API version.
- Clean/silver table: normalized records such as GitHub commits, pull requests, reviews, Jira issues.
- Analytics/gold table: derived metrics such as cycle time, review latency, deployment frequency, work allocation, bottlenecks.

Possible partition columns:

- `tenant_id`
- date/time bucket such as `event_date` or `ingested_date`
- `source` such as `github` or `jira` (if shared table)
- `resource_type` such as `commit`, `pull_request`, `issue`

Caution:

- Do not over-partition. Partitioning by high-cardinality or deeply nested dimensions can create too many small files.
- In lakehouse systems, a practical design often uses date partitioning plus tenant/source clustering, sorting, Z-ordering, or file-level statistics depending on the engine.
- Tenant partitioning sounds intuitive but should be verified against actual query patterns, tenant counts, table size, and engine behavior.

Schema evolution scenario:

- GitHub changes an API response shape multiple times.
- Raw payloads should preserve original source responses and API/schema version metadata.
- Normalized tables should provide a stable analytical contract where possible.
- New fields can be added as nullable columns.
- Breaking changes may require versioned transformation logic or compatibility views.

Interview-ready phrasing:

> I would separate immutable raw ingestion from normalized models. Raw records preserve the original payload, tenant, source, resource type, ingestion timestamp, and source schema/API version. The modeled layer gives product and analytics code a stable contract, with explicit handling for schema evolution and backfills.

### 7. Observability Expectations

For a multi-tenant product data platform, likely observability areas include:

- Pipeline run success/failure by tenant/source/resource.
- Ingestion freshness and lag.
- Queue depth and consumer lag, if event-driven.
- API rate-limit usage and error rates.
- Backfill status.
- Data quality checks by asset/partition.
- SLA dashboards for customer-facing data freshness.
- Logs with tenant/source/run correlation IDs.
- Alerts to Slack/PagerDuty-like systems.
- Metrics for cost and noisy-neighbor behavior.

Possible open-source tools to practice locally:

- Prometheus for metrics.
- Grafana for dashboards.
- OpenTelemetry for traces/metrics/logs instrumentation.
- Loki or OpenSearch for logs.
- Dagster UI for orchestration observability.

### 8. Jellyfish-Specific Assumptions to Verify

The conversation included these assumptions or recollections:

- Jellyfish is an engineering intelligence platform.
- Its product integrates with sources like Jira, GitHub, and CI/CD systems.
- A Staff Data Engineer there may work on customer-facing product data, not only internal analytics.
- Recruiter mentioned a team of roughly five data engineers.
- Recruiter mentioned something like "Jellyfish 2.0".
- The company may use Delta Lake.
- Public/company-reported traction numbers may include hundreds of companies and large counts of engineers/PRs.

These need verification through:

- Job description.
- Recruiter follow-up.
- Hiring-manager interview questions.
- Public engineering blogs/talks, if any.
- Company docs, case studies, and product pages.

Good interview questions:

- What does "Jellyfish 2.0" mean technically and product-wise?
- Is the Staff Data Engineer role closer to ingestion, modeling, platform, or product analytics serving?
- What are the primary data sources and hardest ingestion problems?
- How is tenant isolation represented in storage and compute?
- What orchestration system do you use, and what made it necessary?
- How do you manage schema evolution from external APIs?
- How do you think about batch vs event-driven ingestion?
- What does data freshness mean to customers?
- What observability tells you a customer's data is healthy?

## Learning Agenda

### Must Understand Conceptually

- Terraform basics: providers, resources, modules, state, variables, outputs.
- Multi-tenant design tradeoffs: DB/schema/table/partition isolation.
- Dagster basics: assets, partitions, sensors, schedules, backfills.
- Lakehouse basics: Parquet, object storage, Delta transaction log, Iceberg metadata.
- Ingestion basics: API polling, webhooks, queues, idempotency, retries, rate limits.
- Observability basics: freshness, lag, errors, retries, DLQ, tenant-scoped metrics.

### Hands-On Project Direction

Build a local "mini-Jellyfish" learning platform:

1. **Mock tenants**
   - Create a few fake customer tenants.
   - Each tenant has GitHub-like events and maybe Jira-like issues.

2. **Ingestion**
   - Batch path: poll a mock GitHub API or read fixture files.
   - Event path: accept webhook-like events and push to a local queue.
   - Track tenant, source, resource type, cursor, and ingestion timestamp.

3. **Storage**
   - Raw layer stores immutable JSON payloads.
   - Modeled layer stores normalized commit/PR/issue tables.
   - Use Delta Lake or Iceberg locally if feasible; otherwise use Parquet first and document what is missing.

4. **Orchestration**
   - Use Dagster assets for raw ingestion, normalization, and metrics.
   - Add partitions by date and/or tenant.
   - Add a sensor for queued events and a schedule for reconciliation.

5. **IaC**
   - Use Terraform and/or Docker Compose to define local services.
   - Include MinIO for S3-compatible object storage if using object-store-like paths.
   - Include queue service, orchestration service, and observability services.

6. **Analytics/Product Metrics**
   - Produce metrics like PR cycle time, review latency, commits over time, build failure rate, issue throughput.
   - Ensure every query is tenant-scoped.

7. **Observability**
   - Track ingestion lag, failures, retries, and freshness by tenant/source.
   - Create at least one dashboard or report.

## Interview Positioning

Possible honest framing:

> My current work has given me strong experience with reliable internal analytics pipelines, SQL transformation practices, declarative permissions, CI-based scheduling, and operational alerting. What I'm actively deepening now is the product-data-platform side: multi-tenant isolation, infrastructure as code, lakehouse formats, and asset-aware orchestration. I understand why those become essential when the data platform is the customer-facing product rather than only internal reporting.

## Follow-Up Research Needed

- Verify Jellyfish public customer/traction numbers from primary sources.
- Search for Jellyfish engineering blogs, talks, podcasts, or job postings that mention their stack.
- Verify whether Jellyfish uses Delta Lake, Dagster, Terraform, dbt, Spark, Databricks, Snowflake, or other tooling.
- Research current local Delta Lake options that do not require Spark.
- Research DuckDB's current Delta/Iceberg support.
- Compare Delta Lake vs Iceberg internals with source-backed notes.
- Decide the first local project slice to implement.

## Related Records

- `.loom/knowledge/project-purpose.md`
