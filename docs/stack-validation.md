# Stack Validation

This note records the concrete local stack selected by ticket `.loom/tickets/2026-06-18-validate-delta-dagster-github-stack.md`.

## Selected Stack

| Concern | Selection | Rationale |
| --- | --- | --- |
| Python runtime | Python 3.11+ | Available locally, supported by Dagster and Delta Lake Python libraries, and modern enough for typed Python without chasing newest-runtime incompatibilities. |
| Package/runtime management | `uv` | Project instructions prefer `uv` for Python. It gives fast, reproducible local environments and can run narrow validation commands without committing a full scaffold yet. |
| GitHub ingestion/extraction | `dlt` REST helpers against GitHub REST API | Makes dlthub/dlt the required ingestion layer while still keeping pagination, headers, rate-limit handling, and API versions visible in the project wrapper. |
| Delta Lake library | `deltalake` Python package (`delta-rs`) with `pyarrow` tables | Open-source, local-first, no Spark/JVM requirement for the early portfolio loop, and exposes real Delta transaction-log behavior. |
| DuckDB query validation | `duckdb` with the `delta` extension and `delta_scan(...)` | Proves the planned query layer can read Delta tables through SQL before replacing Python in-memory filtering. |
| Dagster integration | Dagster software-defined assets materialized locally | Matches the chosen first user-facing surface: Dagster UI. Assets can directly call ingestion/transformation functions and attach metadata such as row counts, paths, and freshness. |
| Portable storage profiles | Local filesystem, MinIO, and Cloudflare R2 shapes | Local remains deterministic for tests; MinIO is the open-source S3-compatible profile; R2 is Chris's remote S3-compatible profile. |
| Deterministic tests | Fixture-driven tests plus optional live GitHub validation | Real GitHub data is valuable for the portfolio demo, but deterministic tests should use committed fixtures/mocked HTTP responses so CI and local validation do not depend on tokens, rate limits, or mutable external state. |

## Validation Proof

Run the proof from the repository root:

```bash
uv run --with deltalake --with pyarrow --with dagster --with dlt --with duckdb \
  python tools/validate_stack.py
```

The script validates four things:

1. Python can write and read a local Delta table via `deltalake`/`pyarrow`.
2. DuckDB can install/load the `delta` extension and query a fixture Delta table with `delta_scan(?)`.
3. GitHub API authentication works through dlt's REST client when `GITHUB_TOKEN` or `GH_TOKEN` is set; if no token is set, the script reports the setup gap without failing the local Delta/Dagster proofs.
4. Dagster can materialize a toy asset that writes and reads the selected Delta storage approach.

## Storage Profile Configuration

Storage profile resolution is centralized in `src/kabuto_kurage/paths.py`.

Key environment variables:

| Variable | Profiles | Purpose |
| --- | --- | --- |
| `KABUTO_STORAGE_PROFILE` | all | `local`, `minio`, or `r2`; defaults to `local`. |
| `KABUTO_DATA_ROOT` | local | Optional local runtime data root; defaults to `.local/data`. |
| `KABUTO_STORAGE_PREFIX` | minio/r2 | Object-store prefix before `delta`; defaults to `kabuto-kurage`. |
| `KABUTO_MINIO_BUCKET` | minio | MinIO bucket name. |
| `KABUTO_MINIO_ENDPOINT_URL` | minio | Endpoint such as `http://localhost:9000`. |
| `KABUTO_MINIO_ACCESS_KEY_ID` | minio | Access key copied from local secret storage/Proton Pass. |
| `KABUTO_MINIO_SECRET_ACCESS_KEY` | minio | Secret key copied from local secret storage/Proton Pass. |
| `KABUTO_R2_BUCKET` | r2 | Cloudflare R2 bucket name. |
| `KABUTO_R2_ACCOUNT_ID` | r2 | Cloudflare account ID copied from Proton Pass. |
| `KABUTO_R2_ACCESS_KEY_ID` | r2 | R2 S3-compatible access key copied from Proton Pass. |
| `KABUTO_R2_SECRET_ACCESS_KEY` | r2 | R2 S3-compatible secret key copied from Proton Pass. |

`delta_table_uri(...)` resolves table locations for all profiles. `delta_table_path(...)` is intentionally local-only and preserves the original filesystem behavior for existing deterministic tests.

## DuckDB Extension and Secret Requirements

Local Delta query validation requires only DuckDB's Delta extension:

```sql
INSTALL delta;
LOAD delta;
SELECT * FROM delta_scan('/path/to/local/delta/table');
```

For S3-compatible object storage, DuckDB also needs object-store credentials. The exact production query module will centralize this later; this ticket documents the required shapes only.

### MinIO placeholder shape

Use DuckDB's S3 secret type against a local MinIO endpoint. Values below are placeholders and must live in ignored env/config, not committed files:

```sql
INSTALL httpfs;
LOAD httpfs;
INSTALL delta;
LOAD delta;
CREATE SECRET kabuto_minio (
  TYPE s3,
  KEY_ID 'KABUTO_MINIO_ACCESS_KEY_ID_PLACEHOLDER',
  SECRET 'KABUTO_MINIO_SECRET_ACCESS_KEY_PLACEHOLDER',
  ENDPOINT 'localhost:9000',
  REGION 'us-east-1',
  URL_STYLE 'path',
  USE_SSL false
);
SELECT * FROM delta_scan('s3://KABUTO_MINIO_BUCKET_PLACEHOLDER/delta/table');
```

Delta writes to MinIO through delta-rs should use storage options equivalent to:

```text
AWS_ACCESS_KEY_ID=<from env>
AWS_SECRET_ACCESS_KEY=<from env>
AWS_ENDPOINT_URL=http://localhost:9000
AWS_REGION=us-east-1
allow_http=true
aws_conditional_put=etag
```

### Cloudflare R2 placeholder shape

Use DuckDB's R2 secret type for R2 paths. Values below are placeholders and must come from Proton Pass or another secret manager into environment variables or ignored local config:

```sql
INSTALL httpfs;
LOAD httpfs;
INSTALL delta;
LOAD delta;
CREATE SECRET kabuto_r2 (
  TYPE r2,
  KEY_ID 'KABUTO_R2_ACCESS_KEY_ID_PLACEHOLDER',
  SECRET 'KABUTO_R2_SECRET_ACCESS_KEY_PLACEHOLDER',
  ACCOUNT_ID 'KABUTO_R2_ACCOUNT_ID_PLACEHOLDER'
);
SELECT * FROM delta_scan('r2://KABUTO_R2_BUCKET_PLACEHOLDER/delta/table');
```

Delta writes to R2 through delta-rs should use storage options equivalent to:

```text
AWS_ACCESS_KEY_ID=<from env>
AWS_SECRET_ACCESS_KEY=<from env>
AWS_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
AWS_REGION=auto
aws_conditional_put=etag
```

Live R2 validation is intentionally optional. If `KABUTO_R2_*` credentials are absent, validation must skip remote checks rather than fail deterministic local tests.

## Fallbacks

- If `deltalake` blocks needed features later, use Spark-backed Delta only as a fallback for specific missing capabilities, not as the default local path.
- If dlt's REST helper surface becomes too narrow for future GitHub sources, add narrow project wrappers around dlt primitives before changing the downstream bronze/silver/gold contracts.
- If local filesystem semantics hide object-store issues, add MinIO in the local IaC phase and keep the table layout compatible with S3-style paths.
- If Dagster asset code becomes too coupled to IO details, introduce thin resources for GitHub and Delta storage after the first asset graph is working.
