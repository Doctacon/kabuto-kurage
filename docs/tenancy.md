# Local Tenancy Model

`kabuto-kurage` models multi-tenancy from the first data-platform slice, even though it runs on a single developer machine.

The goal is not production-grade customer isolation. The goal is to make tenant boundaries explicit enough that ingestion, Delta Lake layout, Dagster assets, and later metrics cannot be designed as accidental single-tenant code.

## Tenant Registry

The committed example registry lives at:

```text
config/tenants.example.yaml
```

Copy it for local edits:

```bash
cp config/tenants.example.yaml config/tenants.local.yaml
export KABUTO_TENANTS_CONFIG=config/tenants.local.yaml
```

`config/tenants.local.yaml` is ignored by git so local owner/repository choices do not have to be committed.

The registry shape is:

```yaml
tenants:
  - tenant_id: personal
    display_name: Personal GitHub Tenant
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners:
          - crlough
        repositories: []
```

Rules:

- `tenant_id` must be a safe logical/path identifier: lowercase letters, digits, and underscores; 3-63 chars; starts with a letter.
- Every tenant must define a GitHub source for this milestone.
- `token_env` is an environment-variable name such as `GITHUB_TOKEN`, **not** a token value.
- GitHub sources must include at least one `owner` or `owner/repository` entry.
- Repository entries must use `owner/name` format.

## Secret References

Committed YAML stores secret references only:

```yaml
token_env: GITHUB_TOKEN
```

The actual token belongs in the local shell or ignored `.env` file:

```bash
GITHUB_TOKEN=...
```

The config loader rejects obvious GitHub token prefixes in `token_env` to catch accidental committed secrets early.

## Local Storage Layout

Tenant-scoped Delta paths are centralized in `kabuto_kurage.paths`.

Conventional shape:

```text
.local/data/delta/tenants/{tenant_id}/{layer}/{source}/{table_name}
```

Examples:

```text
.local/data/delta/tenants/personal/bronze/github/pull_requests
.local/data/delta/tenants/personal/silver/github/pull_requests
.local/data/delta/tenants/personal/gold/github/pr_cycle_time
.local/data/delta/tenants/sandbox/bronze/github/pull_requests
```

This path convention intentionally duplicates `tenant_id` in storage even though later records will also carry `tenant_id` as a column. That redundancy makes local inspection easier and creates a clear guardrail for future ingestion and transformation tickets.

## Alternatives Considered

### Database per tenant

Stronger isolation and easier tenant deletion/export, but too heavy for the local first milestone and not aligned with the immediate Delta Lake learning goal.

### Schema per tenant

Useful in warehouses, but the first storage target is filesystem-backed Delta tables, not a warehouse with schemas.

### Shared tables partitioned only by `tenant_id`

Likely realistic for many analytics systems, but less visible for local learning. This project may still use `tenant_id` columns inside shared/model tables later, but the first convention keeps tenant paths explicit.

### Production secret manager

Appropriate for real customer data, but out of scope for a local portfolio project. Environment-variable references are enough to avoid committed secrets while keeping setup understandable.

## Limitations

- This is logical/local isolation, not a production security boundary.
- It does not implement authentication, authorization, encryption, row-level security, or per-tenant compute quotas.
- Later tickets must continue preserving `tenant_id` in raw, silver, and gold records and add tests that tenant-scoped metrics do not leak cross-tenant data.
