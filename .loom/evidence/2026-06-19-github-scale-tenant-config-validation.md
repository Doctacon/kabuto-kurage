Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-add-github-scale-tenant-config.md, .loom/tickets/2026-06-19-curate-github-scale-repository-corpus.md

# GitHub Scale Tenant Config Validation

## What Was Observed

Added opt-in scale tenant registry:

```text
config/tenants.scale.yaml
```

The default registry remains:

```text
config/tenants.example.yaml
```

Deterministic shape validation confirms:

- tenant count: within 20-30 target;
- repository count: within 45-60 target;
- distinct owner/org count: at least 24;
- repository allowlists are explicit;
- token env references are `GITHUB_TOKEN`;
- no owner discovery scopes are present in scale config;
- no obvious GitHub token prefixes are present in repository fields.

## Procedure

Ran:

```bash
uv run pytest tests/test_tenancy.py -q
uv run ruff check tests/test_tenancy.py
uv run mypy src
```

Observed:

```text
12 passed
All checks passed!
Success: no issues found in 18 source files
```

## What This Supports or Challenges

Supports the claim that the curated corpus can be loaded through the same tenant registry validation as the small config, while remaining opt-in and secret-free.

## Limits

This is deterministic config validation. Live GitHub access was covered by `.loom/evidence/2026-06-19-github-scale-corpus-curation.md`; materialization validation is deferred to `.loom/tickets/2026-06-19-validate-github-scale-demo.md`.
