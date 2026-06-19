Status: open
Created: 2026-06-19
Updated: 2026-06-19
Parent: .loom/tickets/2026-06-19-plan-github-portfolio-scale-demo.md
Depends-On: .loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md, .loom/specs/github-portfolio-scale-demo.md

# Add GitHub Scale Tenant Config

## Scope

Add `config/tenants.scale.yaml` as an opt-in portfolio-scale tenant registry.

Do not change the default tenant config path. `config/tenants.example.yaml` remains the small/default local development config.

## Behavior

`config/tenants.scale.yaml` should:

- contain 20-30 tenant partitions;
- contain 45-60 public repositories total;
- contain at least 24 distinct owners/orgs where practical;
- use explicit repository allowlists only;
- store `token_env: GITHUB_TOKEN`, never token values;
- use safe tenant IDs that describe the tenant source/theme without pretending to be real customers.

Example tenant style:

```yaml
tenants:
  - tenant_id: oss_dagster
    display_name: Dagster OSS Projects
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - dagster-io/dagster
```

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

## Progress and Notes

- 2026-06-19: Opened as child ticket. Depends on curated corpus output.

## Blockers

Blocked on `.loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md`.
