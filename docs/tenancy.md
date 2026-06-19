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

The committed default models three portfolio-style tenant partitions:

| Tenant | Purpose | Repositories |
| --- | --- | --- |
| `personal` | Chris's portfolio repositories | `Doctacon/databox`, `Doctacon/az-hp` |
| `oss_projects` | Friend/open-source reference repository | `z3z1ma/pliny` |
| `sandbox` | Safe public GitHub fixture | `octocat/Hello-World` |

The registry shape is:

```yaml
tenants:
  - tenant_id: personal
    display_name: Personal Portfolio Repositories
    sources:
      github:
        token_env: GITHUB_TOKEN
        api_base_url: https://api.github.com
        owners: []
        repositories:
          - Doctacon/databox
          - Doctacon/az-hp
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

If your GitHub token or object-store credentials live in Proton Pass, copy/export them into environment variables for the current shell session. Do not paste them into committed YAML, docs, screenshots, shell history examples, or Loom evidence. Prefer commands that set variables without echoing their values.

The config loader rejects obvious GitHub token prefixes in `token_env` to catch accidental committed secrets early.

## Storage Profiles and Tenant Layout

Tenant-scoped Delta locations are centralized in `kabuto_kurage.paths`. The default profile is `local`, and it preserves the original filesystem shape:

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

The active profile is selected with `KABUTO_STORAGE_PROFILE`:

| Profile | Purpose | Delta root shape |
| --- | --- | --- |
| `local` | Default deterministic local/test storage. | `.local/data/delta` or `$KABUTO_DATA_ROOT/delta` |
| `minio` | Open-source S3-compatible local object-store profile. | `s3://$KABUTO_MINIO_BUCKET/$KABUTO_STORAGE_PREFIX/delta` |
| `r2` | Cloudflare R2 remote profile for Chris's personal runs. | `s3://$KABUTO_R2_BUCKET/$KABUTO_STORAGE_PREFIX/delta` for delta-rs, `r2://...` for DuckDB |

Object-store profile variables are placeholders in `.env.example` only. Real values should come from Proton Pass or another secret manager into ignored env/local config:

```bash
export KABUTO_STORAGE_PROFILE=minio
export KABUTO_MINIO_BUCKET=kabuto-dev
export KABUTO_MINIO_ENDPOINT_URL=http://localhost:9000
export KABUTO_MINIO_ACCESS_KEY_ID=...       # from Proton Pass/local secret store
export KABUTO_MINIO_SECRET_ACCESS_KEY=...   # from Proton Pass/local secret store

export KABUTO_STORAGE_PROFILE=r2
export KABUTO_R2_BUCKET=your-r2-bucket
export KABUTO_R2_ACCOUNT_ID=...             # from Proton Pass/local secret store
export KABUTO_R2_ACCESS_KEY_ID=...          # from Proton Pass/local secret store
export KABUTO_R2_SECRET_ACCESS_KEY=...      # from Proton Pass/local secret store
```

Do not run commands that print these values back to the terminal. `.env`, `.env.*`, `.local/`, `.dlt/`, `secrets/`, `config/tenants.local.yaml`, and `config/storage.local.yaml` are ignored by git.

The storage convention intentionally duplicates `tenant_id` in the URI/path even though records also carry `tenant_id` as a column. That redundancy makes inspection easier and creates a clear guardrail for future ingestion and transformation tickets.

## Validation Guardrails

Automated tests exercise tenant isolation with distinct two-tenant fixture data across bronze, silver, and gold layers. The expected invariant is:

```text
path tenant_id == every row tenant_id == requested materialization tenant_id
```

Silver and gold materializers now fail closed if a tenant-scoped Delta path contains rows for a different tenant. This protects against local development mistakes such as writing `personal` rows into the `sandbox` path before building downstream tables.

The validation is intentionally local and logical:

- It proves this project's ingestion/transformation code preserves tenant IDs and reads tenant-scoped paths.
- It proves tenant-scoped gold metrics exclude the other fixture tenant's repositories and PR numbers.
- It does **not** provide production authentication, authorization, encryption, row-level security, audit controls, or compute/network isolation.

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
