Status: done
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-scaffold-portfolio-data-platform.md

# Add Local Infrastructure as Code

## Scope

Represent local development infrastructure as code in a way that maps to the Jellyfish role's Terraform/IaC requirement without overengineering.

Possible components:

- Terraform for local files/config, Docker resources, or documented local service provisioning.
- Docker Compose for Dagster services and optional local storage services.
- Optional MinIO if object-store semantics are useful for Delta Lake learning.
- Clear environment variable and secret setup.

## Out of Scope

- Managed cloud infrastructure.
- Kubernetes unless later chosen.
- Production deployment.

## Acceptance Criteria

- The repo contains an IaC directory with a clear purpose.
- README explains what Terraform manages and why.
- Local services can be started reproducibly with documented commands.
- IaC choices are documented honestly, including where Docker Compose is more appropriate than Terraform.

## Current State

Done. The repository now contains honest local Infrastructure as Code that demonstrates Terraform workflow without pretending to run production cloud infrastructure.

Implemented:

- `iac/local/` Terraform module using only the `hashicorp/local` provider.
- Terraform-managed ignored local runtime files:
  - `.local/dagster/dagster.yaml`;
  - `.local/runtime/kabuto.env`;
  - `.local/data/README.md`.
- Optional `iac/local/docker-compose.yml` for running Dagster UI as a local service from the checkout.
- `docs/local-iac.md` and `iac/local/README.md` explaining the Terraform/Docker Compose boundary, commands, generated files, and secret handling.
- README and `docs/development.md` updates for local IaC commands.
- `.gitignore` updates for Terraform provider cache/state/plans while preserving the committed provider lock file.
- `tests/test_local_iac.py` for static IaC validation.

Evidence: `.loom/evidence/2026-06-18-local-iac-validation.md`.

Review: `.loom/reviews/2026-06-18-local-iac-review.md`.

## Journal

- 2026-06-18: Set active and delegated implementation to worker.
- 2026-06-18: Added local Terraform module, generated-file templates, Docker Compose Dagster runner, documentation, and static tests.
- 2026-06-18: Ran Terraform fmt/init/validate/apply successfully; Terraform created three ignored local files under `.local/`.
- 2026-06-18: Validated Docker Compose config with standalone `docker-compose`; local environment did not support the newer `docker compose` plugin command.
- 2026-06-18: Ran `uv run pytest`, `uv run ruff check .`, and `uv run mypy src`; all passed.
- 2026-06-18: Recorded evidence and review, then moved ticket to done.

## Results

Acceptance criteria satisfied:

- The repo contains `iac/local/` with a clear local-only purpose.
- README and docs explain what Terraform manages and why: ignored local Dagster/data/runtime files, not cloud or production infrastructure.
- Local runtime prerequisites can be prepared with documented Terraform commands; optional Dagster service can be run with documented Docker Compose commands.
- IaC choices are honest about boundaries: Terraform prepares local config/files, Docker Compose runs the optional local process, Python/Dagster owns data workflows.
- Secrets remain uncommitted and ignored; generated env file contains no GitHub token value.

## Blockers

None for this ticket. Production deployment, managed cloud resources, Kubernetes, and real secret management remain explicitly out of scope and require future architecture decisions before implementation.
