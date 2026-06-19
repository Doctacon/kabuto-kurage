Status: open
Created: 2026-06-18
Updated: 2026-06-18
Parent: .loom/tickets/2026-06-18-build-mini-engineering-intelligence-platform.md
Depends-On: .loom/tickets/2026-06-18-add-dagster-asset-graph.md, .loom/tickets/2026-06-18-build-gold-engineering-metrics.md, .loom/tickets/2026-06-18-validate-tenant-isolation.md

# Write Portfolio Architecture Docs

## Scope

Create the documentation that makes the project understandable as a portfolio artifact.

Expected docs:

- README with quickstart and project narrative.
- Architecture overview diagram or text diagram.
- Data flow explanation: GitHub API → bronze Delta → silver models → gold metrics → Dagster UI.
- Multi-tenancy explanation.
- Delta Lake learning notes.
- Dagster orchestration notes.
- Jellyfish-relevance section tied to public research, without claiming private knowledge.

## Out of Scope

- Marketing polish beyond accurate portfolio communication.
- Public deployment site.

## Acceptance Criteria

- A reviewer can understand what the project demonstrates within five minutes.
- Setup instructions are accurate against a fresh local checkout.
- Docs distinguish verified Jellyfish public facts from project assumptions.
- Docs include screenshots or instructions for viewing Dagster UI if screenshots are not committed.

## Progress and Notes

- Not started.

## Blockers

- Requires enough implemented behavior to document honestly.
