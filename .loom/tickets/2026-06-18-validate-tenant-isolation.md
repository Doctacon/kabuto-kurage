Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-model-tenants-and-source-config.md, .loom/tickets/2026-06-18-build-gold-engineering-metrics.md

# Validate Tenant Isolation

## Scope

Prove that the local platform's tenant-scoped reads and metrics do not accidentally mix data across tenants.

Expected validation:

- Fixture data for at least two tenants.
- Tests for bronze/silver/gold tenant propagation.
- Negative tests or assertions that tenant A metric queries exclude tenant B data.
- Documentation of the isolation model and its limitations.

## Out of Scope

- Production-grade authorization.
- Encryption or network isolation.
- Claims that this model is sufficient for real customer data without further controls.

## Acceptance Criteria

- Automated tests validate tenant ID propagation across layers.
- Automated tests validate tenant-scoped metrics.
- Documentation clearly distinguishes local logical isolation from production security requirements.
- Any discovered leakage risk is either fixed or tracked in a follow-up ticket.

## Progress and Notes

- Not started.

## Blockers

- Requires metrics or at least silver models to validate end-to-end propagation.
