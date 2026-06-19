Status: recorded
Created: 2026-06-18
Updated: 2026-06-18
Relates-To: .loom/tickets/2026-06-18-add-local-iac.md

# Local IaC Validation Evidence

## What Was Observed

Implemented local-only Infrastructure as Code for `kabuto-kurage`.

Changed implementation/docs/tests:

- `.gitignore`
- `README.md`
- `docs/development.md`
- `docs/local-iac.md`
- `iac/local/README.md`
- `iac/local/versions.tf`
- `iac/local/variables.tf`
- `iac/local/main.tf`
- `iac/local/outputs.tf`
- `iac/local/templates/dagster.yaml.tftpl`
- `iac/local/templates/kabuto.env.tftpl`
- `iac/local/docker-compose.yml`
- `iac/local/.terraform.lock.hcl`
- `tests/test_local_iac.py`
- `.loom/tickets/2026-06-18-add-local-iac.md`

Terraform uses only the `hashicorp/local` provider. It prepares ignored local runtime files under `.local/`:

- `.local/dagster/dagster.yaml`
- `.local/runtime/kabuto.env`
- `.local/data/README.md`

Docker Compose is optional and runs the local Dagster service from the checkout. Tests do not require Docker or a Docker daemon.

## Procedure

Validation commands run from the repository root:

```bash
terraform -chdir=iac/local fmt -check
terraform -chdir=iac/local init -backend=false
terraform -chdir=iac/local validate
terraform -chdir=iac/local apply -auto-approve
docker-compose --env-file .local/runtime/kabuto.env -f iac/local/docker-compose.yml config --quiet
uv run pytest
uv run ruff check .
uv run mypy src
git status --short
```

Note: the newer `docker compose` plugin command was unavailable in this local environment, so validation used the installed standalone `docker-compose` command. Docs mention the plugin as an equivalent when available.

## Validation Output

Terraform init/validate:

```text
Terraform has been successfully initialized!
Success! The configuration is valid.
```

Terraform apply:

```text
Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:
dagster_home = ".../.local/dagster"
dagster_url = "http://localhost:3000"
data_root = ".../.local/data"
runtime_env_file = ".../.local/runtime/kabuto.env"
```

Docker Compose config validation:

```text
# no output; exit 0
```

`uv run pytest`:

```text
collected 41 items
...
41 passed in 2.48s
```

`uv run ruff check .`:

```text
All checks passed!
```

`uv run mypy src`:

```text
Success: no issues found in 12 source files
```

`git status --short` showed expected unstaged/untracked source, docs, tests, IaC, ticket, evidence, and review files only.

## What This Supports or Challenges

Supports closing `.loom/tickets/2026-06-18-add-local-iac.md` because:

- The repo has a clear `iac/local/` directory.
- Terraform local provider config validates and applies locally.
- Generated runtime files are under ignored `.local/` paths and contain no GitHub token value.
- Docker Compose config validates without starting services.
- README and docs explain what Terraform manages, what Docker Compose manages, and why the boundary exists.
- Tests assert the IaC is local-only, has expected entrypoints, and does not define cloud/Kubernetes resources.

## Limits

This evidence does not prove production deployment, cloud infrastructure, Kubernetes, managed object storage, or a running Docker service. Those are explicitly out of scope for this ticket.
