Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Target: .loom/tickets/2026-06-19-migrate-github-bronze-ingestion-to-dlt.md
Verdict: pass

# Review: dlt GitHub Bronze Ingestion Migration

## Target

Current diff for `.loom/tickets/2026-06-19-migrate-github-bronze-ingestion-to-dlt.md`, including:

- `src/kabuto_kurage/ingestion/github_bronze.py`
- `tests/test_github_bronze_ingestion.py`
- `tools/validate_stack.py`
- `pyproject.toml` / `uv.lock`
- README and docs updates
- migration decision/ticket/evidence records

## Findings

### Pass: dlt is now the extraction layer

`GitHubRestClient` now wraps dlt's `RESTClient` and configures `HeaderLinkPaginator` plus `BearerTokenAuth`. The hand-rolled `while url: client.get(...)` pagination loop and custom `Link` parser were removed.

### Pass: downstream contracts are preserved

The migration did not change:

- `BRONZE_SCHEMA`
- tenant-scoped Delta table paths
- overwrite write semantics
- `GitHubBronzeIngestionResult`
- bronze record payload/rate-limit fields
- silver/gold/Dagster/API/MCP files or contracts

### Pass: deterministic tests cover the important ingestion behavior

`tests/test_github_bronze_ingestion.py` now uses a local `requests` adapter to drive dlt `RESTClient` with fixture responses. Tests cover:

- dlt `RESTClient` + `HeaderLinkPaginator` selection;
- header-link pagination;
- rate-limit header capture;
- raw payload preservation;
- idempotent overwrite Delta writes;
- no fake token values in result/Delta row output.

### Pass: docs no longer present direct httpx as the ingestion layer

README, architecture, stack validation, and bronze ingestion docs now identify dlt REST helpers as the GitHub ingestion/extraction layer. Historical Loom records still mention the old `httpx` decision, but they are temporal records and the new decision supersedes that direction.

## Verdict

Pass. The implementation satisfies the ticket scope and preserves the existing downstream contracts.

## Residual Risk

- Live GitHub extraction through dlt was not exercised because no local GitHub token was available during validation; deterministic dlt-backed tests passed.
- dlt now emits a local runtime warning about `XDG_DATA_HOME`/`~/.dlt` in this environment. It is non-failing but may appear in test output on this machine.
- The project uses dlt for extraction/pagination only; Delta writes remain project-owned by explicit decision. Future work could evaluate dlt destinations if desired.
