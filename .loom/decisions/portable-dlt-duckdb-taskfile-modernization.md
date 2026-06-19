Status: active
Created: 2026-06-19
Updated: 2026-06-19

# Portable dlt + DuckDB + Taskfile Modernization

Supersedes: `.loom/decisions/superseded/use-dlt-for-github-ingestion.md`

## Context

After the MVP and export-surface milestones, Chris clarified several architecture preferences:

- storage should support his Cloudflare R2 instance;
- storage should remain portable and open-source-first rather than R2-only;
- bronze ingestion should be more dlt-native and less manually schema-shaped;
- the query layer should use DuckDB instead of Python in-memory filtering;
- the developer-facing command workflow should use Taskfile rather than direct Python script invocations;
- his GitHub API token lives in Proton Pass, but secrets must still not be committed, logged, or printed.

Public docs/source findings in `.loom/research/2026-06-19-portable-dlt-duckdb-storage-research.md` indicate that dlt supports filesystem/S3-compatible destinations, DuckDB can scan Delta tables locally and remotely with `delta_scan`, Cloudflare R2 is accessible through S3-compatible APIs, and MinIO is a viable open-source local object-store profile.

## Decision

The next architecture pass will modernize the platform around four choices:

1. **Portable storage profiles**
   - Local filesystem remains the default and deterministic test target.
   - MinIO becomes the open-source local S3-compatible profile.
   - Cloudflare R2 becomes Chris's remote S3-compatible profile.
   - The code/docs should talk in terms of storage profiles, not R2-only assumptions.

2. **dlt-native bronze ingestion**
   - GitHub bronze ingestion should move from a project-owned raw-envelope-first schema toward explicit dlt source/resource/schema/state behavior.
   - Raw payload auditability should be preserved or intentionally replaced with documented dlt schema/state artifacts.

3. **DuckDB-backed query layer**
   - REST and MCP exports should query gold Delta tables through DuckDB SQL rather than loading all rows into Python for filtering/aggregation.
   - DuckDB must remain tenant-scoped and must not expose raw bronze payloads or secrets.

4. **Taskfile developer workflow**
   - `Taskfile.yml` becomes the primary user-facing command surface.
   - Existing Python scripts may remain as implementation entrypoints behind tasks.

## Alternatives Considered

### Make Cloudflare R2 the only supported storage target

Rejected. R2 is useful for Chris's personal runs, but an R2-only design would undercut the open-source-first/self-hostable principle. MinIO and local filesystem keep the architecture portable.

### Keep current manually shaped bronze envelope

Rejected as the target direction. It is auditable and stable, but Chris explicitly wants more automation and a more dlt-native ingestion story.

### Keep Python query filtering

Rejected. It works for local fixtures but is not the stronger data-platform architecture. DuckDB SQL over Delta is more realistic and more educational.

### Replace all Python scripts with Taskfile tasks

Rejected. Taskfile should be the user-facing workflow, but Python scripts can remain useful narrow entrypoints for tests, Dagster assets, and implementation reuse.

## Consequences

- Existing docs/specs need updates to describe storage profiles, dlt-native bronze, DuckDB query execution, and Taskfile commands.
- The old dlt decision is superseded because it intentionally preserved a mostly manual bronze schema; this milestone revisits that tradeoff.
- Object-store credentials must be handled carefully through ignored env/config files.
- Early validation must prove DuckDB, Delta, dlt, and S3-compatible storage work together before broad implementation.
- Downstream contract changes may be required if dlt-native bronze alters table shape; those changes should be isolated behind silver models and validated with tests.
