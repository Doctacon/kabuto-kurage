Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-scaffold-portfolio-data-platform.md

# Model Tenants and Source Configuration

## Scope

Define the configuration model that makes the project explicitly multi-tenant from the beginning.

Expected design elements:

- Tenant registry with at least two tenant entries.
- GitHub source configuration per tenant.
- Secret references without committed secrets.
- Storage path conventions by tenant/source/layer.
- Validation rules for tenant IDs.
- Documentation explaining the tenancy model and alternatives not chosen.

## Out of Scope

- Full access-control system.
- Production secret manager.
- Database-per-tenant or schema-per-tenant implementations unless chosen during execution.

## Acceptance Criteria

- Tenant/source config exists in a reviewable code or YAML format.
- At least two tenants can be configured without duplicating code.
- Tests or validation catch missing/invalid tenant IDs.
- Documentation states how tenant isolation is represented in this local project.

## Current State

Done. Tenant/source configuration is represented in committed YAML and loaded through validated Python helpers.

Implemented:

- `config/tenants.example.yaml` with two tenant entries: `personal` and `sandbox`.
- `src/kabuto_kurage/tenancy.py` for YAML loading, tenant registry access, tenant ID validation, GitHub source validation, and secret-reference validation.
- Tenant-scoped Delta path helpers in `src/kabuto_kurage/paths.py` using `.local/data/delta/tenants/{tenant_id}/{layer}/{source}/{table_name}`.
- `docs/tenancy.md` explaining local logical isolation, secret references, storage conventions, alternatives considered, and limitations.
- README and `.env.example` updates for tenant config setup.
- Tests covering valid default config, env path override, invalid tenant IDs, duplicate tenant IDs, missing GitHub source, accidental token values in `token_env`, missing source scope, invalid repository names, and tenant-scoped path conventions.

Evidence: `.loom/evidence/2026-06-18-tenant-config-validation.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added tenant/source YAML, tenancy loader/validation code, tenant-scoped storage path helpers, tenancy docs, README/env/gitignore updates, and tests.
- 2026-06-18: Ran `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run mypy src`, and a tenant-registry sanity command successfully.
- 2026-06-18: Recorded validation evidence and moved ticket to done.

## Results

Acceptance criteria satisfied:

- Tenant/source config exists in `config/tenants.example.yaml`.
- Two tenants can be configured through the same YAML schema and loader without duplicated code.
- Tests and loader validation catch missing/invalid tenant IDs and other invalid source configuration.
- `docs/tenancy.md` documents local tenant isolation, storage path conventions, alternatives, and limitations.
- Secret references are stored as environment-variable names only; committed YAML contains no token values and validation rejects obvious GitHub token prefixes.

## Blockers

None for this ticket. Real GitHub ingestion remains intentionally deferred to `.loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md`.
