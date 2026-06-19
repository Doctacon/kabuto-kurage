Status: active
Created: 2026-06-19
Updated: 2026-06-19

# Portable dlt + DuckDB Lakehouse Workflow

## Purpose and Scope

This spec defines the next architecture milestone for `kabuto-kurage`: modernize storage, ingestion, querying, and developer workflow while preserving the portfolio narrative already built.

The goal is to make the platform feel more like a realistic local/cloud-portable data lakehouse:

- storage can run on local filesystem, MinIO, or Cloudflare R2 profiles;
- bronze ingestion is dlt-native instead of mostly manually shaped by project code;
- REST/MCP export queries run through DuckDB SQL over Delta gold tables;
- day-to-day commands are exposed through Taskfile;
- secrets such as GitHub/R2 tokens remain outside git and outside logs.

## Storage Profiles

The system should support three profile classes.

### Local filesystem profile

- Default for tests and easiest local development.
- Uses `.local/data/...` or `KABUTO_DATA_ROOT`-derived paths.
- Requires no object-store credentials.
- Must remain deterministic for unit/integration tests.

### MinIO profile

- Open-source S3-compatible local object-store profile.
- Used to validate object-store behavior without depending on proprietary infrastructure.
- Should be runnable through local IaC/Docker Compose where practical.
- Should use ignored local credentials/config.

### Cloudflare R2 profile

- Chris's remote S3-compatible object-store profile.
- Must use environment variables or ignored local config for account ID, access key, secret, endpoint/bucket, and related settings.
- Must not be required for tests.
- Must not print or commit credentials.

The project should use profile names in docs and config, for example:

```text
local
minio
r2
```

## dlt-Native Bronze Ingestion

GitHub remains the first source.

The next ingestion design should use dlt source/resource concepts more directly than the current wrapper. Expected properties:

- explicit GitHub dlt source/resources for repositories and pull requests;
- dlt-controlled schema/state artifacts are visible and documented;
- pagination/auth/rate-limit behavior remains testable;
- tenant identity is preserved in every persisted record or path;
- raw payload auditability is either preserved explicitly or replaced with documented dlt-normalized/raw-source artifacts;
- downstream silver models are the boundary that adapt dlt bronze output into stable analytical tables.

The migration must be incremental enough that a reviewer can understand old-vs-new behavior and tests can prove no cross-tenant leak.

## DuckDB Query Layer

The export query layer should use DuckDB SQL over gold Delta tables.

Required behavior:

- REST and MCP contracts remain stable unless a spec update explicitly changes them.
- Tenant ID validation remains mandatory before any query path is constructed.
- Queries must scan only the requested tenant's gold Delta paths.
- Filters and pagination should be expressed in SQL, not Python list filtering.
- Summary aggregation should be expressed in SQL where practical.
- DuckDB extension setup and object-storage secrets should be encapsulated in a small project query/storage module.
- Responses must remain JSON-serializable and must not include raw bronze payloads or secrets.

## Taskfile Developer Workflow

`Taskfile.yml` should become the primary user-facing command surface.

Expected tasks include:

```text
task setup
task test
task lint
task typecheck
task validate
task dagster
task ingest -- tenant=sandbox
task silver -- tenant=sandbox
task gold -- tenant=sandbox
task observe -- tenant=sandbox
task api
task mcp
```

Exact Task syntax may vary, but the docs should teach Taskfile first and direct Python scripts second.

## Proton Pass Secret Workflow

The project should not directly integrate with Proton Pass in this milestone.

Docs should say:

- store GitHub/R2 secrets in Proton Pass or another password manager;
- export secrets into the shell as environment variables before running tasks;
- never commit `.env`, `.local/`, dlt secrets, R2 tokens, or GitHub tokens;
- avoid commands that echo token values.

## Acceptance Criteria

A future implementation satisfies this spec when:

1. Storage profile config exists for `local`, `minio`, and `r2`, with local deterministic tests and documented R2 setup.
2. dlt-native GitHub source/resources replace or supersede the manually shaped bronze extraction path.
3. dlt schema/state behavior is documented and covered by tests or evidence.
4. Silver/gold/Dagster/export surfaces continue to work or are intentionally migrated with tests.
5. REST/MCP query layer uses DuckDB SQL against gold Delta tables.
6. Tenant isolation tests still prove tenant A cannot read tenant B data.
7. Taskfile is the documented primary command runner.
8. Docs include safe Proton Pass/environment-variable guidance without direct secret-manager coupling.
9. Full validation passes: `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Non-Goals

- Production OAuth/SSO or hosted secret management.
- R2-only architecture.
- Removing all Python CLI scripts.
- Supporting every dlt destination or every object-storage provider.
- Rewriting metrics semantics unless required by the dlt-native bronze migration.
- Public deployment.

## Related Records

- `.loom/research/2026-06-19-portable-dlt-duckdb-storage-research.md`
- `.loom/decisions/portable-dlt-duckdb-taskfile-modernization.md`
- `.loom/specs/mini-engineering-intelligence-platform.md`
- `.loom/specs/engineering-metrics-export-surface.md`
