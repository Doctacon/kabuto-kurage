Status: superseded
Created: 2026-06-19
Updated: 2026-06-19

# Use dlt for GitHub Ingestion

Superseded-By: `.loom/decisions/portable-dlt-duckdb-taskfile-modernization.md`

## Context

The initial MVP implemented GitHub bronze ingestion with a small direct REST client. The user clarified that data ingestion must use [dlt](https://dlthub.com/) / `dlthub`, and that this is a hard project requirement.

The project still needs to preserve earlier portfolio goals:

- local, open-source-first tooling;
- GitHub API as the first source;
- tenant-scoped bronze Delta tables;
- visible pagination, rate-limit metadata, raw payload retention, and deterministic tests;
- Dagster as the first orchestration UI.

`dlt` is open source and provides REST API helpers, including a REST client and GitHub-style header-link pagination support. The project can use `dlt` for API extraction while continuing to write the curated project bronze schema to Delta Lake with `deltalake`/`pyarrow`.

## Decision

GitHub bronze ingestion must use `dlt` for the REST extraction layer.

The project will adopt dlt's REST client / pagination helpers for GitHub API reads and keep the existing tenant-scoped bronze Delta schema and downstream silver/gold contracts stable.

## Alternatives Considered

### Keep direct `httpx` ingestion

Rejected. It conflicts with the user's explicit requirement that ingestion use dlt.

### Use dlt to own both extraction and storage

Not chosen for this migration. The current project already has a deliberate Delta Lake table layout, bronze schema, and downstream contracts. The lowest-risk migration is to use dlt where it matters for ingestion/extraction while preserving the existing Delta write path.

This can be revisited later if a future milestone wants dlt pipelines/destinations to own more of the load path.

## Consequences

- `dlt` becomes a first-class runtime dependency.
- Docs and stack validation must describe dlt as the ingestion layer, not direct `httpx` ingestion.
- Tests should prove the GitHub client uses dlt REST/pagination primitives while preserving previous bronze table behavior.
- Some lower-level HTTP behavior may now be mediated by dlt's helper abstractions rather than hand-rolled request loops.
