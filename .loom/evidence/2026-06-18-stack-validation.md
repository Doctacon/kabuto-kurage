Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md

# Stack Validation Evidence

## What Was Observed

Ran the stack validation proof script after executing ticket `.loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md`.

Command:

```bash
uv run --with deltalake --with pyarrow --with dagster --with httpx python tools/validate_stack.py
```

Observed results:

- Delta Lake local write/read passed.
- `_delta_log/00000000000000000000.json` was created for the proof table.
- Dagster materialized toy asset `toy_delta_stack_validation` successfully.
- GitHub live API validation was skipped because neither `GITHUB_TOKEN` nor `GH_TOKEN` was present.

Key output:

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

## Procedure

The command used ephemeral dependencies through `uv run --with ...` and wrote proof Delta tables under a temporary directory.

## What This Supports or Challenges

Supports closing the stack-validation ticket because the selected local Delta/Dagster stack works. It also records that live authenticated GitHub API validation remains dependent on an operator-provided token.

## Limits

This evidence does not prove the full ingestion pipeline works. It only proves narrow local stack compatibility and that missing GitHub token handling is visible.
