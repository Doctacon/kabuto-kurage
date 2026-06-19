Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Target: .loom/tickets/2026-06-19-migrate-bronze-to-dlt-native-github-source.md
Verdict: pass

# dlt-Native GitHub Bronze Source Review

## Target

Review of the current diff for `.loom/tickets/2026-06-19-migrate-bronze-to-dlt-native-github-source.md`:

- `src/kabuto_kurage/ingestion/github_bronze.py`
- `tests/test_github_bronze_ingestion.py`
- `tests/test_dagster_assets.py`
- `docs/github-bronze-ingestion.md`
- ticket/evidence records

## Findings

### Pass: dlt concepts are now explicit

The ingestion module now exposes a dlt source named `github_bronze` and dlt resources named `repositories` and `pull_requests`. Tests inspect the resource names, write disposition, primary/column hints, and generated schema artifacts. This is a meaningful step beyond only wrapping `RESTClient`.

### Pass: downstream contracts remain stable

The implementation preserves the existing tenant-scoped Delta bronze table layout and `payload_json` raw-audit contract. Silver, tenant-isolation, Dagster, gold, REST, and MCP tests pass through the full suite.

### Pass: token leakage risk is tested

Tests assert the fake token is not present in ingestion result dictionaries, Delta rows, dlt schema artifacts, or dlt state artifacts.

### Minor residual concern: dlt state artifact is a local snapshot, not a full dlt pipeline state store

The code updates dlt source/resource state during resource iteration and writes an explicit local `state.json` inspection artifact. It does not run a dlt pipeline destination and does not rely on dlt's persistent pipeline state mechanism. This is acceptable for the current ticket because it keeps existing Delta contracts stable, but docs/evidence should continue to describe it as an inspection snapshot rather than full production dlt state management.

### Minor residual concern: dlt destination ownership remains deferred

The ticket intentionally does not move Delta writes into dlt destinations. This is consistent with scope, but future storage-profile work may revisit whether dlt should own more of the load path.

## Verdict

Pass. The change satisfies the ticket scope and preserves downstream behavior.

## Residual Risk

- Live GitHub extraction was not exercised in this ticket's evidence.
- The dlt state artifact is not a substitute for production-grade dlt pipeline state persistence.
- Object-storage writes are not implemented here.
