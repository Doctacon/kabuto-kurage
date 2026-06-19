Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/specs/mini-engineering-intelligence-platform.md, .loom/decisions/initial-portfolio-architecture.md

# Validate Delta + Dagster + GitHub Stack

## Scope

Resolve the highest-risk technical choices before broad implementation.

This ticket should determine the concrete local stack for:

- Python package/runtime management.
- GitHub API client approach.
- Delta Lake read/write library.
- Dagster integration pattern.
- Local object/filesystem storage for Delta tables.
- Test strategy for deterministic fixtures alongside real GitHub API runs.

## Out of Scope

- Building the full ingestion pipeline.
- Implementing all Dagster assets.
- Creating production deployment infrastructure.

## Acceptance Criteria

- A short architecture note or ticket progress entry names the selected libraries and why they were chosen.
- A minimal proof exists that Python can write and read a local Delta table.
- A minimal proof exists that GitHub API access works with a token, or the expected setup failure is clearly documented.
- A minimal proof exists that Dagster can materialize a toy asset touching the selected storage approach.
- Risks and fallback options are recorded.

## Current State

Done. The local stack has been validated sufficiently to unblock downstream scaffold and implementation tickets.

Selected stack:

- **Python runtime:** Python 3.11+.
- **Package/runtime management:** `uv`.
- **GitHub API client:** direct GitHub REST API calls with `httpx`.
- **Delta Lake library:** `deltalake` Python package (`delta-rs`) with `pyarrow` tables.
- **Dagster integration pattern:** Dagster software-defined assets materialized locally.
- **Local storage:** local filesystem Delta table paths first; defer MinIO/S3-compatible storage to local IaC if object-store realism is needed.
- **Deterministic tests:** fixture-driven/mocked tests for CI and repeatability, with optional live GitHub validation when `GITHUB_TOKEN` or `GH_TOKEN` is present.

Supporting architecture note: `docs/stack-validation.md`.

Validation proof script: `tools/validate_stack.py`.

## Journal

- 2026-06-18: Set active and delegated implementation/validation to worker.
- 2026-06-18: Added `docs/stack-validation.md` documenting selected libraries, rationale, validation command, and fallback options.
- 2026-06-18: Added `tools/validate_stack.py`, a narrow proof that writes/reads Delta locally, checks GitHub token setup, and materializes a Dagster asset that touches Delta storage.
- 2026-06-18: Ran `uv run --with deltalake --with pyarrow --with dagster --with httpx python tools/validate_stack.py` successfully. Delta proof passed with 2 rows and `_delta_log/00000000000000000000.json`; Dagster materialization succeeded; GitHub live API validation was skipped because no `GITHUB_TOKEN` or `GH_TOKEN` was set in the environment.
- 2026-06-18: Moved ticket to done because the only missing live evidence is an expected operator-secret setup condition and is documented explicitly.

## Results

Validation output summary:

```json
{
  "dagster": {
    "asset": "toy_delta_stack_validation",
    "rows": 2,
    "status": "passed"
  },
  "delta": {
    "delta_log_files": [
      "00000000000000000000.json"
    ],
    "rows": 2,
    "status": "passed",
    "version": 0
  },
  "github": {
    "setup": "Set GITHUB_TOKEN or GH_TOKEN to validate authenticated GitHub API access.",
    "status": "skipped_missing_token"
  },
  "python": {
    "package_runner": "uv run --with ...",
    "runtime": "python3"
  }
}
```

## Risks and Fallback Options

- **GitHub token not present during validation:** Live authenticated GitHub proof is documented as skipped. Downstream ingestion tickets must require `GITHUB_TOKEN` or `GH_TOKEN` for real API runs and should use mocked/fixture tests for repeatability.
- **`deltalake` feature gaps:** If later requirements need features unavailable in delta-rs, evaluate Spark-backed Delta only for that gap rather than making Spark the default local path.
- **Local filesystem hides object-store behavior:** Start with local paths for speed; add MinIO/S3-compatible storage during IaC work if object-store semantics become important.
- **Direct `httpx` calls can become repetitive:** Prefer a small internal GitHub client wrapper before adopting a high-level SDK, so pagination/rate-limit behavior remains explicit.
- **Dagster asset coupling:** If asset bodies become too coupled to IO details, introduce thin Dagster resources after the first asset graph exists.

## Blockers

None for this validation ticket. Downstream live GitHub ingestion remains dependent on the operator providing `GITHUB_TOKEN` or `GH_TOKEN`.
