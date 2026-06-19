Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-modernize-storage-ingestion-query-dev-workflow.md
Depends-On: .loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md

# Migrate Bronze to dlt-Native GitHub Source

## Scope

Move GitHub bronze ingestion from a mostly project-shaped raw envelope to a more dlt-native source/resource/schema/state implementation.

Expected behavior:

- Define explicit dlt GitHub source/resources for repositories and pull requests.
- Let dlt own more schema/resource/state behavior.
- Preserve tenant identity in persisted records or tenant-scoped paths.
- Preserve raw payload auditability or document the replacement dlt-normalized/raw-source artifact.
- Keep silver models as the compatibility boundary between source layout and analytics models.
- Keep pagination, rate-limit handling, idempotency/incrementality, and token safety testable.

## Out of Scope

- Adding new GitHub resource types beyond repositories and pull requests unless needed for dlt design.
- Changing gold metric semantics.
- Requiring live GitHub credentials in deterministic tests.
- Rewriting REST/MCP contracts.

## Acceptance Criteria

- GitHub ingestion uses dlt source/resource/schema/state concepts directly.
- Tests prove tenant isolation, pagination, rate-limit metadata or equivalent observability, no token leakage, and repeat-run behavior.
- Silver model tests pass or are intentionally adapted to the new bronze layout.
- Docs explain dlt schema/state artifacts and how to inspect them.
- Full downstream test/lint/typecheck validation passes.

## Progress and Notes

- Not started.

## Blockers

- Requires storage profile conventions to avoid refactoring paths twice.
