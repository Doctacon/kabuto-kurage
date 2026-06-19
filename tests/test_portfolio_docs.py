from __future__ import annotations

from pathlib import Path

README = Path("README.md")
ARCHITECTURE = Path("docs/architecture.md")


def test_portfolio_readme_points_reviewer_to_core_story() -> None:
    readme = README.read_text(encoding="utf-8")

    required_phrases = [
        "What a reviewer should notice in five minutes",
        "GitHub API",
        "Bronze Delta Lake",
        "Silver Delta Lake",
        "Gold Delta Lake",
        "Dagster UI",
        "Multi-tenancy",
        "Local Infrastructure as Code",
        "Jellyfish relevance: verified facts vs assumptions",
    ]
    for phrase in required_phrases:
        assert phrase in readme


def test_architecture_doc_covers_required_portfolio_surfaces() -> None:
    architecture = ARCHITECTURE.read_text(encoding="utf-8")

    required_sections = [
        "## Five-Minute Map",
        "## Data Flow",
        "## Multi-Tenancy Model",
        "## Delta Lake Learning Notes",
        "## Observability",
        "## Local Infrastructure as Code",
        "## Jellyfish Relevance: Verified Facts vs Project Assumptions",
        "## Validation Posture",
    ]
    for section in required_sections:
        assert section in architecture


def test_docs_distinguish_public_jellyfish_facts_from_unverified_internals() -> None:
    docs = README.read_text(encoding="utf-8") + "\n" + ARCHITECTURE.read_text(encoding="utf-8")

    assert "Verified public facts" in docs
    assert "Not verified" in docs
    assert "does not claim to reproduce Jellyfish's private architecture" in docs

    forbidden_unverified_claims = [
        "Jellyfish uses Dagster",
        "Jellyfish uses Delta Lake",
        "Jellyfish uses this exact storage layout",
        "Jellyfish's internal orchestrator is Dagster",
    ]
    for claim in forbidden_unverified_claims:
        assert claim not in docs


def test_readme_documentation_links_exist() -> None:
    readme = README.read_text(encoding="utf-8")
    expected_docs = [
        "docs/architecture.md",
        "docs/development.md",
        "docs/stack-validation.md",
        "docs/tenancy.md",
        "docs/github-bronze-ingestion.md",
        "docs/github-silver-models.md",
        "docs/github-gold-metrics.md",
        "docs/dagster-asset-graph.md",
        "docs/observability.md",
        "docs/local-iac.md",
    ]

    for doc_path in expected_docs:
        assert doc_path in readme
        assert Path(doc_path).exists(), f"README links to missing doc: {doc_path}"
