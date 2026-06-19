from __future__ import annotations

from pathlib import Path

README = Path("README.md")
ARCHITECTURE = Path("docs/architecture.md")
BRONZE = Path("docs/github-bronze-ingestion.md")
STACK = Path("docs/stack-validation.md")
EXPORT_API = Path("docs/export-api.md")
LOCAL_IAC = Path("docs/local-iac.md")
DEVELOPMENT = Path("docs/development.md")

MODERNIZED_DOCS = [README, ARCHITECTURE, BRONZE, STACK, EXPORT_API, LOCAL_IAC, DEVELOPMENT]


def docs_text() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in MODERNIZED_DOCS)


def test_modernized_docs_cover_storage_profiles_dlt_duckdb_and_taskfile() -> None:
    docs = docs_text()

    required_phrases = [
        "Storage profiles",
        "KABUTO_STORAGE_PROFILE=local",
        "KABUTO_STORAGE_PROFILE=minio",
        "KABUTO_STORAGE_PROFILE=r2",
        "MinIO",
        "Cloudflare R2",
        "dlt source/resources",
        "schema.json",
        "state.json",
        "DuckDB SQL",
        "delta_scan(...) ".strip(),
        "Taskfile",
        "task validate",
        "task ingest tenant=sandbox",
        "task api",
        "task mcp",
    ]
    for phrase in required_phrases:
        assert phrase in docs


def test_modernized_docs_preserve_secret_handling_boundary() -> None:
    docs = docs_text()

    required_phrases = [
        "Proton Pass",
        "exported into your shell",
        "never commit",
        "do not echo",
        "environment variables",
        "ignored local config",
    ]
    for phrase in required_phrases:
        assert phrase in docs

    forbidden_secret_examples = [
        "ghp_",
        "github_pat_",
        "AKIAIOSFODNN7EXAMPLE",
        "wJalrXUtnFEMI",
        "KABUTO_R2_ACCOUNT_ID=123",
        "echo $GITHUB_TOKEN",
        "echo ${GITHUB_TOKEN}",
        "echo $KABUTO_R2_SECRET_ACCESS_KEY",
        "echo ${KABUTO_R2_SECRET_ACCESS_KEY}",
    ]
    for secret_fragment in forbidden_secret_examples:
        assert secret_fragment not in docs


def test_modernized_docs_preserve_jellyfish_boundary() -> None:
    docs = docs_text()

    required_phrases = [
        "does not claim to reproduce Jellyfish's private architecture",
        "not Jellyfish-compatible",
        "not a claim that Jellyfish uses",
        "Not verified publicly by this project",
    ]
    for phrase in required_phrases:
        assert phrase in docs

    forbidden_claims = [
        "Jellyfish uses Dagster",
        "Jellyfish uses Delta Lake",
        "Jellyfish uses DuckDB",
        "Jellyfish uses dlt",
        "Jellyfish uses Cloudflare R2",
        "Jellyfish's internal tenant model is this allowlist model",
        "These metrics reproduce Jellyfish proprietary metrics",
    ]
    for claim in forbidden_claims:
        assert claim not in docs
