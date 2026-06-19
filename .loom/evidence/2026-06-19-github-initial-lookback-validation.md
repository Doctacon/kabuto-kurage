Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-add-github-initial-lookback-window.md, .loom/specs/github-portfolio-scale-demo.md

# GitHub Initial Lookback Validation

## What Was Observed

Implemented first-run PR history bounding with:

```bash
KABUTO_GITHUB_INITIAL_LOOKBACK_DAYS=180
```

When the env var is set and no per-repository incremental cursor exists, GitHub PR ingestion now uses `fetched_at - initial_lookback_days` as the default `updated_at` cutoff. Existing per-repository cursor state still takes precedence and continues to use `KABUTO_GITHUB_INCREMENTAL_LOOKBACK_DAYS`.

## Procedure

Ran deterministic validation:

```bash
uv run pytest tests/test_github_bronze_ingestion.py -q
uv run ruff check src/kabuto_kurage/ingestion/github_bronze.py tests/test_github_bronze_ingestion.py
uv run mypy src
```

Observed:

```text
8 passed, 1 warning
All checks passed!
Success: no issues found in 18 source files
```

The new test `test_initial_lookback_limits_first_pull_request_scan` uses a mocked GitHub API with a linked second page. The first PR page includes one PR inside the 180-day cutoff and one older PR. The test asserts:

- only the recent PR is written to bronze;
- the old PR is filtered out;
- page 2 is not fetched even though GitHub supplied a `Link: rel="next"` header.

## What This Supports or Challenges

Supports the claim that portfolio-scale first runs can be bounded to a 180-day history window rather than crawling all historical pull requests for every repository.

## Limits

This is deterministic API mocking, not a live scale run. Live GitHub validation is deferred to `.loom/tickets/2026-06-19-validate-github-scale-demo.md` after the scale config exists.
