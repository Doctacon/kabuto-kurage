Status: open
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

## Progress and Notes

- Not started.

## Blockers

- Requires scaffold. May be sequenced after core platform if needed.
