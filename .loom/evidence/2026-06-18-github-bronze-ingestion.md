Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md

# GitHub Bronze Ingestion Evidence

## What Was Observed

Implemented GitHub REST API ingestion for repositories and pull requests into tenant-scoped bronze Delta tables.

Changed implementation/docs/tests:

- `src/kabuto_kurage/ingestion/__init__.py`
- `src/kabuto_kurage/ingestion/github_bronze.py`
- `tools/ingest_github_bronze.py`
- `tests/test_github_bronze_ingestion.py`
- `docs/github-bronze-ingestion.md`
- `docs/development.md`
- `README.md`
- `.loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md`

## Procedure

Validation commands run from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

Live validation was also run using an existing `gh auth token` without printing or committing the token. The command used a temporary tenant config and data root for `octocat/Hello-World`:

```bash
# Token was supplied through command substitution and was not printed.
export GITHUB_TOKEN="$(gh auth token)"
KABUTO_TENANTS_CONFIG="$cfg" uv run python tools/ingest_github_bronze.py --tenant sandbox --data-root "$tmpdir/data" --max-repositories 1
```

## Validation Output

`uv run pytest`:

```text
collected 18 items

tests/test_github_bronze_ingestion.py ....
tests/test_scaffold.py ...
tests/test_tenancy.py ...........

18 passed in 0.61s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 6 source files
```

Live GitHub validation summary:

```json
{
  "tenant_id": "sandbox",
  "repository_count": 1,
  "pull_request_count": 1646,
  "writes": [
    {"resource_type": "repositories", "row_count": 1},
    {"resource_type": "pull_requests", "row_count": 1646}
  ],
  "rate_limit_snapshots": 18
}
```

The full live output included multiple pull-request pages, proving pagination and per-response rate-limit capture.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-ingest-github-to-bronze-delta.md` because:

- A configured tenant can ingest GitHub repositories and pull requests into bronze Delta tables.
- Deterministic tests cover raw payload to bronze record normalization, pagination, rate-limit capture, Delta writes, and idempotent overwrite behavior.
- Live validation against GitHub wrote one repository and 1,646 pull request rows for a configured tenant.
- Documentation explains API limits, failure behavior, pagination, rate-limit capture, and overwrite semantics.

## Limits

This evidence does not prove silver transformations, Dagster asset graph integration, metrics, retries, webhook/event ingestion, or incremental cursor processing. Those are explicitly out of scope for this ticket and tracked by downstream tickets.
