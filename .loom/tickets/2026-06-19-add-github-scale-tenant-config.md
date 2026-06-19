Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md, .loom/specs/github-portfolio-scale-demo.md

# Add GitHub Scale Tenant Config

## Scope

Add `config/tenants.scale.yaml` as an opt-in portfolio-scale tenant registry.

Do not change the default tenant config path. `config/tenants.example.yaml` remains the small/default local development config.

## Behavior

`config/tenants.scale.yaml`:

- contains 25 tenant partitions;
- contains 50 public repositories total;
- contains 42 distinct owners/orgs;
- uses explicit repository allowlists only;
- stores `token_env: GITHUB_TOKEN`, never token values;
- uses safe tenant IDs that describe the tenant source/theme without pretending to be real customers.

## Acceptance Criteria

- `config/tenants.scale.yaml` exists and loads through `load_tenant_registry(path)`.
- Deterministic tests validate:
  - tenant count target;
  - repo count target;
  - distinct owner/org count target;
  - unique tenant IDs;
  - no owner discovery in scale config unless intentionally justified;
  - no committed token values;
  - all repo strings match `owner/name`.
- Existing tests for `config/tenants.example.yaml` continue to pass.
- Docs or test names make clear that the scale config is opt-in.
- Validation passes: `uv run pytest`, `uv run ruff check .`, `uv run mypy src`.

## Current State

Done. Evidence recorded in `.loom/evidence/2026-06-19-github-scale-tenant-config-validation.md`.

## Progress and Notes

- 2026-06-19: Opened as child ticket. Depends on curated corpus output.
- 2026-06-19: Set active after curation completed.
- 2026-06-19: Added `config/tenants.scale.yaml` from the YAML-ready corpus in `.loom/evidence/2026-06-19-github-scale-corpus-curation.md`.
- 2026-06-19: Added deterministic scale config shape validation to `tests/test_tenancy.py`.
- 2026-06-19: Ran targeted tests, ruff, and mypy; all passed.

## Results

Acceptance criteria satisfied.

## Blockers

None.
