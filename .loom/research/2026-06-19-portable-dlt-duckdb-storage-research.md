Status: done
Created: 2026-06-19
Updated: 2026-06-19

# Portable dlt + DuckDB + Object Storage Research

## Question

How should the next `kabuto-kurage` architecture pass support portable object storage profiles, more dlt-native bronze ingestion, DuckDB-backed query execution, and Taskfile-based developer ergonomics without violating the project's open-source-first preference or breaking the existing portfolio story?

## Sources and Methods

- Existing project records:
  - `.loom/specs/mini-engineering-intelligence-platform.md`
  - `.loom/specs/engineering-metrics-export-surface.md`
  - `.loom/decisions/superseded/use-dlt-for-github-ingestion.md`
- Existing implementation files:
  - `src/kabuto_kurage/ingestion/github_bronze.py`
  - `src/kabuto_kurage/queries/github_metrics.py`
  - `src/kabuto_kurage/paths.py`
  - `src/kabuto_kurage/api/app.py`
  - `src/kabuto_kurage/mcp_server.py`
- Documentation/source-search findings:
  - dlt filesystem destination supports local/remote filesystems and S3-compatible storage, including Cloudflare R2 and MinIO through fsspec-style configuration. It supports table formats including Delta and provides DuckDB-dialect dataset access.
  - DuckDB's `delta` extension supports `delta_scan(...)` over local and remote Delta tables and can use secrets for S3 credentials.
  - DuckDB has Cloudflare R2 guidance using S3-compatible API support and `TYPE r2` secrets with `KEY_ID`, `SECRET`, and `ACCOUNT_ID`.
  - DuckDB `httpfs` S3 API support is tested with MinIO and notes S3-compatible systems such as Cloudflare R2 should work, with service-specific caveats.
  - delta-rs documentation for S3-like storage covers Cloudflare R2 and MinIO and recommends conditional puts (`aws_conditional_put = etag`) for safe concurrent writes on compatible stores.

## Findings

### Storage

A portable profile model best matches the project principles:

- local filesystem remains the lowest-friction default and deterministic test target;
- MinIO is the open-source S3-compatible local object-store profile;
- Cloudflare R2 is a personal remote profile using the same S3-compatible abstraction.

R2 should not become the only supported target because the project has an explicit open-source-first/self-hostable preference. Treating R2 as one profile avoids lock-in while still letting Chris use his real R2 bucket.

### dlt-native bronze

The current system uses dlt REST helpers for extraction but still owns a manually shaped bronze envelope schema. That satisfied the first dlt requirement but does not fully teach dlt source/resource/schema/state behavior.

The next design should make GitHub ingestion more dlt-native by introducing explicit dlt source/resource definitions, visible dlt schema/state artifacts, and a storage layout that can be written through dlt where practical. The existing raw-payload audit need remains valuable, so the migration should explicitly decide how raw payload visibility survives if dlt normalization creates multiple tables.

### DuckDB query layer

The existing query layer reads Delta tables into Python and filters in memory. DuckDB SQL over Delta tables is a stronger data-engineering story and better supports the future R2/MinIO path. DuckDB's `delta_scan` plus `httpfs`/S3/R2 secrets are the right direction, but object-store credentials and extension behavior need focused validation before broad refactoring.

### Taskfile developer UX

Python CLI scripts can remain implementation entrypoints, but the user-facing workflow should be `Taskfile.yml`. It should wrap common flows such as setup, validation, Dagster, ingestion, transforms, observability, API, and MCP. This lowers cognitive load without deleting the Python scripts that tests and internals can still call.

### Proton Pass token workflow

The app should not integrate directly with Proton Pass yet. The safe boundary is documentation: keep reading `GITHUB_TOKEN`/`GH_TOKEN`; document that Chris can copy/export the token from Proton Pass into the shell. Avoid commands that echo token values.

## Conclusions

Recommended next milestone: **Modernize Storage, Ingestion, Query, and Developer Workflow**.

Implement as a parent plan with child tickets:

1. Validate object storage + DuckDB + dlt stack against local filesystem, MinIO, and planned R2 profile.
2. Add storage profiles and secret-safe configuration conventions.
3. Migrate bronze ingestion toward dlt-native source/resources/schema/state.
4. Replace the export query layer with DuckDB SQL over Delta gold tables.
5. Add Taskfile as the primary developer workflow.
6. Update portfolio docs and evidence to explain the modernized architecture.

Key risks to validate early:

- Delta Lake writes to R2/MinIO require correct storage options and conditional-put semantics.
- DuckDB `delta_scan` over object storage may require extension installation, `httpfs`, and correctly scoped secrets.
- dlt-native normalized output may require downstream silver model adaptation.
- R2 credentials must never be committed or printed.
