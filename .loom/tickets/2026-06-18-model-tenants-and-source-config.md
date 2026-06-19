Status: open
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

## Progress and Notes

- Not started.

## Blockers

- Requires scaffold.
