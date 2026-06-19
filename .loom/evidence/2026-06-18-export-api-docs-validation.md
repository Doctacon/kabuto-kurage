Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-document-and-validate-export-api.md, .loom/specs/engineering-metrics-export-surface.md

# Export API Documentation Validation

## What Was Observed

The REST export API documentation was expanded and validated after the tenant-scoped API implementation existed.

Changed documentation now includes:

- setup and run commands for `uv run uvicorn kabuto_kurage.api.app:app --reload`;
- both supported local token configuration paths: `KABUTO_API_TOKENS_JSON` and ignored YAML via `KABUTO_API_TOKENS_CONFIG`;
- curl examples for each specified endpoint;
- response examples for throughput, cycle time, summary, and auth/query errors;
- a table mapping each endpoint to its existing gold Delta metric inputs;
- tenant-scoped access expectations, including `401` and `403` behavior;
- a public Jellyfish inspiration boundary that explicitly rejects Jellyfish API compatibility and internal-architecture claims.

Validation commands run from repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Observed validation output summary:

```text
62 passed, 1 warning in 2.40s
All checks passed!
Success: no issues found in 17 source files
 M .loom/tickets/2026-06-18-document-and-validate-export-api.md
 M README.md
 M docs/architecture.md
 M docs/export-api.md
 M tests/test_portfolio_docs.py
?? tests/test_export_api_docs.py
```

The one pytest warning came from FastAPI/Starlette test-client dependency deprecation text and did not fail the suite.

## Procedure

1. Read the export surface spec, ticket, API implementation, existing API tests, README, architecture docs, and current export API docs.
2. Updated portfolio docs to make the implemented REST export API visible and accurate.
3. Added deterministic documentation checks in `tests/test_export_api_docs.py` and updated existing portfolio-doc checks.
4. Ran full test, lint, and typecheck commands.
5. Recorded this evidence and a pass review.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-document-and-validate-export-api.md` because:

- README/docs contain endpoint setup and curl examples.
- Docs state the API is inspired by public Jellyfish API/export evidence but is not Jellyfish-compatible.
- Each endpoint is mapped to existing gold metric tables.
- Tenant-scoped access and auth error behavior are documented.
- Tests validate the docs continue to include those portfolio-critical claims.
- Existing test/lint/typecheck suite passed.

## Limits

This evidence does not prove a live deployed API server was manually called with `curl`; endpoint behavior itself is covered by deterministic FastAPI `TestClient` tests in `tests/test_export_rest_api.py`. No MCP wrapper was implemented during this ticket.
