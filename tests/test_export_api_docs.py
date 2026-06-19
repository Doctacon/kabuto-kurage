from __future__ import annotations

from pathlib import Path

EXPORT_API = Path("docs/export-api.md")
README = Path("README.md")
ARCHITECTURE = Path("docs/architecture.md")

ENDPOINTS = [
    "/api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily",
    "/api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time",
    "/api/v1/tenants/{tenant_id}/metrics/github/summary",
]


def test_export_api_docs_map_each_endpoint_to_gold_tables() -> None:
    docs = EXPORT_API.read_text(encoding="utf-8")

    for endpoint in ENDPOINTS:
        assert endpoint in docs

    assert "gold/github/pr_throughput_daily" in docs
    assert "gold/github/pr_cycle_time" in docs
    assert "src/kabuto_kurage/queries/github_metrics.py" in docs


def test_export_api_docs_include_setup_curl_responses_and_errors() -> None:
    docs = EXPORT_API.read_text(encoding="utf-8")

    required_phrases = [
        "uv run uvicorn kabuto_kurage.api.app:app --reload",
        "KABUTO_API_TOKENS_JSON",
        "KABUTO_API_TOKENS_CONFIG",
        "curl -H \"Authorization: Bearer $SANDBOX_EXPORT_API_TOKEN\"",
        "Example response",
        "Missing Authorization bearer token",
        "Invalid bearer token",
        "Token is not allowed to access tenant sandbox",
        "end_date must be greater than or equal to start_date",
    ]
    for phrase in required_phrases:
        assert phrase in docs


def test_export_api_docs_capture_tenant_scope_and_jellyfish_boundary() -> None:
    docs = "\n".join(
        [
            EXPORT_API.read_text(encoding="utf-8"),
            README.read_text(encoding="utf-8"),
            ARCHITECTURE.read_text(encoding="utf-8"),
        ]
    )

    required_phrases = [
        "Each token maps",
        "explicit tenant allowlist",
        "The API never defaults to all tenants",
        "not a compatible Jellyfish API",
        "not Jellyfish-compatible",
        "claim Jellyfish uses FastAPI",
    ]
    for phrase in required_phrases:
        assert phrase in docs

    forbidden_claims = [
        "Jellyfish's API is compatible with these endpoints",
        "Jellyfish's internal API is implemented with FastAPI",
        "Jellyfish's internal tenant model is this allowlist model",
        "These metrics reproduce Jellyfish proprietary metrics",
    ]
    for claim in forbidden_claims:
        assert claim not in docs
