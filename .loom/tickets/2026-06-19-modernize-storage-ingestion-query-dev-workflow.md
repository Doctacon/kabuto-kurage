Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: none
Depends-On: .loom/specs/portable-dlt-duckdb-lakehouse-workflow.md, .loom/decisions/portable-dlt-duckdb-taskfile-modernization.md

# Modernize Storage, Ingestion, Query, and Developer Workflow

## Scope

Parent plan for the next architecture milestone: make `kabuto-kurage` more realistic and ergonomic by adding portable storage profiles, moving bronze ingestion toward dlt-native source/resources, replacing Python in-memory export queries with DuckDB SQL, and adding Taskfile as the primary command surface.

This parent ticket coordinates child tickets. It is not directly executable.

## Desired End State

- Local filesystem remains the default deterministic profile.
- MinIO validates open-source S3-compatible object storage locally.
- Cloudflare R2 is documented/configurable as Chris's remote S3-compatible profile.
- GitHub bronze ingestion uses more dlt-native source/resource/schema/state behavior.
- REST/MCP export queries use DuckDB SQL over gold Delta tables.
- `Taskfile.yml` becomes the user-facing workflow for setup, validation, Dagster, ingestion, transforms, observability, API, and MCP.
- Proton Pass remains outside the code; docs explain safe env-var export without logging secrets.

## Child Tickets

1. `.loom/tickets/2026-06-19-validate-portable-storage-duckdb-dlt-stack.md`
   - Prove the technical stack before broad refactors.
   - Validate local Delta + DuckDB `delta_scan`, MinIO/R2 config shape, dlt filesystem/S3-compatible options, and required storage options.

2. `.loom/tickets/2026-06-19-add-storage-profiles-and-secret-conventions.md`
   - Add storage profile config abstractions for `local`, `minio`, and `r2`.
   - Keep secrets outside git.
   - Document Proton Pass/env-var workflow.

3. `.loom/tickets/2026-06-19-migrate-bronze-to-dlt-native-github-source.md`
   - Replace/supersede the current manual bronze extraction wrapper with explicit dlt GitHub source/resources/schema/state behavior.
   - Preserve tenant identity and downstream silver boundary.

4. `.loom/tickets/2026-06-19-query-gold-metrics-with-duckdb.md`
   - Replace Python in-memory query filtering/aggregation with DuckDB SQL over gold Delta tables.
   - Preserve REST/MCP contracts and tenant isolation.

5. `.loom/tickets/2026-06-19-add-taskfile-developer-workflow.md`
   - Add `Taskfile.yml` and docs-first command ergonomics.
   - Keep Python scripts as implementation entrypoints if useful.

6. `.loom/tickets/2026-06-19-update-modernized-portfolio-docs.md`
   - Update README/architecture/docs after implementation to explain storage profiles, dlt-native bronze, DuckDB query layer, Taskfile workflow, and secret handling.

## Sequencing

Recommended order:

1. Validate stack first. Do not refactor until child 1 resolves the storage/query/dlt compatibility risks.
2. Add storage profiles and secret conventions.
3. Migrate bronze ingestion to dlt-native source/resources.
4. Move query layer to DuckDB once storage-path conventions are stable.
5. Add Taskfile once command targets are known.
6. Final docs update after implementation details settle.

DuckDB query work and Taskfile work may proceed in parallel after storage profiles are clear, but dlt-native bronze migration should avoid racing storage-profile changes.

## Acceptance Criteria

The parent plan can move to done when:

- All child tickets are done or explicitly superseded.
- `.loom/specs/portable-dlt-duckdb-lakehouse-workflow.md` acceptance criteria are satisfied.
- Full validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.
- Evidence exists for stack validation and final milestone validation.
- Docs make the new architecture understandable to a portfolio reviewer.

## Progress and Notes

- 2026-06-19: Created from user-approved shaping choices: portable storage profiles, dlt-native bronze, DuckDB query layer now, and Taskfile workflow.

## Blockers

- Implementation should not start until the user approves executing this plan.
