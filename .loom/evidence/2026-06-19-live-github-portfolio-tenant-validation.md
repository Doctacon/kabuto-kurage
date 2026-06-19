Status: recorded
Created: 2026-06-19
Updated: 2026-06-19
Relates-To: .loom/tickets/2026-06-19-configure-live-github-portfolio-tenants.md

# Live GitHub Portfolio Tenant Validation

## Scope

Validated the portfolio-style GitHub tenant configuration against live GitHub data using the Proton Pass item `GitHub API Token`, field `API Key`, as a local `GITHUB_TOKEN`. The token value was not printed or committed.

## Repository Access Check

All configured repositories returned HTTP 200 from the GitHub repository endpoint:

- `Doctacon/databox`
- `Doctacon/az-hp`
- `z3z1ma/pliny`
- `octocat/Hello-World`

## Live Dagster Materialization

Successful live Dagster materialization runs:

```bash
task materialize TENANT=personal
task materialize TENANT=oss_projects
```

Both completed with `RUN_SUCCESS` while passing the token through the environment only for the local command.

## Observed Rows

`personal` tenant after live materialization:

```text
bronze/repositories: rows=2 freshness=fresh
bronze/pull_requests: rows=33 freshness=fresh
silver/repositories: rows=2 freshness=fresh
silver/pull_requests: rows=33 freshness=fresh
gold/pr_throughput_daily: rows=5 freshness=fresh
gold/pr_cycle_time: rows=33 freshness=fresh
```

`oss_projects` tenant after live materialization:

```text
bronze/repositories: rows=1 freshness=fresh
bronze/pull_requests: rows=8 freshness=fresh
silver/repositories: rows=1 freshness=fresh
silver/pull_requests: rows=8 freshness=fresh
gold/pr_throughput_daily: rows=6 freshness=fresh
gold/pr_cycle_time: rows=8 freshness=fresh
```

## Deterministic Validation

Commands run after config/docs/test updates:

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

Observed:

```text
87 passed, 2 warnings
All checks passed!
Success: no issues found in 18 source files
```

## Limits

This is still a local portfolio validation, not a production deployment. It validates live GitHub access, explicit repository allowlists, Dagster materialization, Delta writes, and observability for selected tenants. It does not add GitHub App auth, incremental sync, schedules, retries, production secret management, or cloud infrastructure.
