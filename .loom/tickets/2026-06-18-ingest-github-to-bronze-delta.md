Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-model-tenants-and-source-config.md

# Ingest GitHub to Bronze Delta

## Scope

Build the first real ingestion path from GitHub API to raw/bronze Delta Lake tables.

Initial resources:

- Repositories.
- Pull requests.

Expected behavior:

- Authenticate with GitHub token from environment/local secret.
- Handle pagination.
- Capture basic rate-limit information when available.
- Persist raw API payloads with metadata: `tenant_id`, source, resource type, fetched timestamp, source identifiers, and ingestion run ID.
- Make repeated runs idempotent or document duplicate-handling limitations.

## Out of Scope

- Complex transformations.
- Full webhook/event ingestion.
- All GitHub resource types.

## Acceptance Criteria

- A configured tenant can ingest GitHub repositories and pull requests into bronze Delta tables.
- Raw records preserve the original payload or enough source JSON for schema-evolution learning.
- Basic tests cover payload normalization into bronze records using fixtures.
- Execution notes document API limits and failure behavior.

## Progress and Notes

- Not started.

## Blockers

- Requires tenant/source config.
