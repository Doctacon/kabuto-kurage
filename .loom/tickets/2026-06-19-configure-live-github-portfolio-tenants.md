Status: done
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-add-dagster-materialization-smoke-tests.md

# Configure Live GitHub Portfolio Tenants

## Scope

Use the user-selected fine-grained GitHub PAT from Proton Pass and explicit repository allowlists to make the local Dagster demo look more production-like with real public repositories and portfolio-style tenant partitions.

## Inputs

- `personal` tenant repositories:
  - `Doctacon/databox`
  - `Doctacon/az-hp`
- `oss_projects` tenant repositories:
  - `z3z1ma/pliny`
- `sandbox` tenant repositories:
  - `octocat/Hello-World`
- Token source: Proton Pass item `GitHub API Token`, field `API Key`; use only as a local `GITHUB_TOKEN`, do not print or commit it.

## Acceptance Criteria

- Tenant config exposes portfolio-style tenants with explicit repository allowlists and no token values.
- Tests/documentation reflect the portfolio tenant shape.
- Live GitHub access is validated without printing the token.
- At least one live materialization path is run with the Proton Pass token.
- Full deterministic validation passes.

## Journal

- 2026-06-19: User provided explicit repo allowlists.
- 2026-06-19: Validated token can access all configured repos: `Doctacon/databox`, `Doctacon/az-hp`, `z3z1ma/pliny`, and `octocat/Hello-World` returned HTTP 200.
- 2026-06-19: Renamed the non-personal public repo tenant from `community` to `oss_projects` at user request.
- 2026-06-19: Live materialized `personal` and `oss_projects` with the Proton Pass token passed through `GITHUB_TOKEN` only for the local command.
- 2026-06-19: Recorded evidence in `.loom/evidence/2026-06-19-live-github-portfolio-tenant-validation.md`.

## Results

Acceptance criteria satisfied:

- Tenant config exposes `personal`, `oss_projects`, and `sandbox` with explicit repository allowlists and no token values.
- Tests/documentation reflect the portfolio tenant shape.
- Live GitHub access was validated without printing the token.
- Live Dagster materialization succeeded for `personal` and `oss_projects`.
- Deterministic validation passed: `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`.

## Blockers

None.
