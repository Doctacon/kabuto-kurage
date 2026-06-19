# Local IaC

This directory contains local-only Infrastructure as Code for `kabuto-kurage`.

## Purpose

The Terraform here demonstrates the IaC workflow used in larger data-platform environments while staying honest about this repository's scope. It prepares reproducible local files and directories under ignored `.local/` paths:

- `.local/dagster/dagster.yaml`
- `.local/runtime/kabuto.env`
- `.local/data/README.md`

It does **not** create cloud resources, managed services, Kubernetes objects, databases, networks, or secrets.

## Commands

From the repository root:

```bash
terraform -chdir=iac/local init
terraform -chdir=iac/local apply
terraform -chdir=iac/local output
```

Optional validation:

```bash
terraform -chdir=iac/local fmt -check
terraform -chdir=iac/local validate
```

## Optional Docker Compose

Terraform prepares local config; Docker Compose runs the optional Dagster process:

```bash
docker-compose --env-file .local/runtime/kabuto.env -f iac/local/docker-compose.yml up dagster
```

Do not put token values in Terraform files or generated templates. Export `GITHUB_TOKEN` or `GH_TOKEN` in your shell when live GitHub ingestion is needed. If your environment has the newer Docker Compose plugin instead of the standalone command, use `docker compose` with the same arguments.

See `../../docs/local-iac.md` for full context and boundaries.
