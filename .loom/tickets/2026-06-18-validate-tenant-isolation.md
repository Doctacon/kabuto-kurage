Status: done
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

## Current State

Done. Explicit end-to-end tenant isolation validation now covers bronze, silver, and gold layers.

Implemented:

- `tests/test_tenant_isolation.py` creates distinct two-tenant fixture data for `sandbox` and `personal`, materializes silver and gold for both tenants, and asserts each tenant's bronze/silver/gold rows contain only that tenant ID.
- Tenant-scoped gold metrics are validated to exclude the other tenant's repositories and PR numbers.
- Silver materialization now fails closed if a tenant-scoped bronze Delta path contains rows for another `tenant_id`.
- Gold materialization now fails closed if a tenant-scoped silver Delta path contains rows for another `tenant_id`.
- `docs/tenancy.md` documents local logical isolation validation and distinguishes it from production security boundaries.

Evidence: `.loom/evidence/2026-06-18-tenant-isolation-validation.md`.

Review: `.loom/reviews/2026-06-18-tenant-isolation-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added end-to-end two-tenant isolation tests across bronze, silver, and gold.
- 2026-06-18: Added tenant ID mismatch guards in silver and gold materializers to fail closed on corrupted tenant-scoped paths.
- 2026-06-18: Updated tenancy docs with validation guardrails and production-security limitations.
- 2026-06-18: Ran `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`; all passed.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- Automated tests validate tenant ID propagation across bronze, silver, and gold layers.
- Automated tests validate tenant-scoped metrics exclude other tenants.
- Documentation clearly distinguishes local logical isolation from production security requirements.
- A discovered leakage risk from mismatched tenant rows in tenant-scoped paths was fixed by adding fail-closed materialization guards.

## Blockers

None for this ticket. Production authentication, authorization, encryption, RLS, and audit controls remain out of scope and require future architecture decisions before implementation.
