# Stack Validation

This note records the concrete local stack selected by ticket `.loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md`.

## Selected Stack

| Concern | Selection | Rationale |
| --- | --- | --- |
| Python runtime | Python 3.11+ | Available locally, supported by Dagster and Delta Lake Python libraries, and modern enough for typed Python without chasing newest-runtime incompatibilities. |
| Package/runtime management | `uv` | Project instructions prefer `uv` for Python. It gives fast, reproducible local environments and can run narrow validation commands without committing a full scaffold yet. |
| GitHub API client | `httpx` against GitHub REST API | Keeps pagination, headers, rate-limit handling, API versions, and retries explicit for learning large-scale third-party integration patterns. Avoids hiding important integration behavior behind a high-level wrapper. |
| Delta Lake library | `deltalake` Python package (`delta-rs`) with `pyarrow` tables | Open-source, local-first, no Spark/JVM requirement for the early portfolio loop, and exposes real Delta transaction-log behavior. |
| Dagster integration | Dagster software-defined assets materialized locally | Matches the chosen first user-facing surface: Dagster UI. Assets can directly call ingestion/transformation functions and attach metadata such as row counts, paths, and freshness. |
| Local storage | Local filesystem paths for Delta tables first | Lowest-friction proof of lakehouse semantics. MinIO/S3-compatible object storage can be added later when IaC/local-infrastructure tickets need object-store realism. |
| Deterministic tests | Fixture-driven tests plus optional live GitHub validation | Real GitHub data is valuable for the portfolio demo, but deterministic tests should use committed fixtures/mocked HTTP responses so CI and local validation do not depend on tokens, rate limits, or mutable external state. |

## Validation Proof

Run the proof from the repository root:

```bash
uv run --with deltalake --with pyarrow --with dagster --with httpx \
  python tools/validate_stack.py
```

The script validates three things:

1. Python can write and read a local Delta table via `deltalake`/`pyarrow`.
2. GitHub API authentication works when `GITHUB_TOKEN` or `GH_TOKEN` is set; if no token is set, the script reports the setup gap without failing the local Delta/Dagster proofs.
3. Dagster can materialize a toy asset that writes and reads the selected Delta storage approach.

## Fallbacks

- If `deltalake` blocks needed features later, use Spark-backed Delta only as a fallback for specific missing capabilities, not as the default local path.
- If direct `httpx` GitHub calls become repetitive, wrap them in a small internal client rather than adopting a high-level GitHub SDK first.
- If local filesystem semantics hide object-store issues, add MinIO in the local IaC phase and keep the table layout compatible with S3-style paths.
- If Dagster asset code becomes too coupled to IO details, introduce thin resources for GitHub and Delta storage after the first asset graph is working.
