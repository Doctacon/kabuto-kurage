from __future__ import annotations

from pathlib import Path

import pytest

from kabuto_kurage.paths import PROJECT_ROOT, delta_table_path, tenant_delta_root
from kabuto_kurage.tenancy import (
    TenantConfigError,
    load_tenant_registry,
    tenant_config_path,
    validate_env_var_name,
    validate_tenant_id,
)


def write_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "tenants.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def test_default_registry_has_portfolio_github_tenants() -> None:
    registry = load_tenant_registry()

    assert registry.tenant_ids == ("oss_projects", "personal", "sandbox")
    assert registry.get("personal").github.token_env == "GITHUB_TOKEN"
    assert registry.get("personal").github.owners == ()
    assert registry.get("personal").github.repositories == (
        "Doctacon/databox",
        "Doctacon/az-hp",
    )
    assert registry.get("oss_projects").github.repositories == ("z3z1ma/pliny",)
    assert registry.get("sandbox").github.repositories == ("octocat/Hello-World",)


def test_tenant_config_path_can_be_overridden(monkeypatch, tmp_path: Path) -> None:
    configured = tmp_path / "tenants.local.yaml"
    monkeypatch.setenv("KABUTO_TENANTS_CONFIG", str(configured))

    assert tenant_config_path() == configured.resolve()


def test_tenant_id_validation_rejects_missing_or_path_unsafe_values() -> None:
    assert validate_tenant_id("tenant_123") == "tenant_123"

    for invalid in ["", "Atenant", "ab", "tenant-a", "tenant/a", "../tenant"]:
        with pytest.raises(TenantConfigError):
            validate_tenant_id(invalid)


def test_loader_rejects_duplicate_tenant_ids(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
        tenants:
          - tenant_id: personal
            display_name: First
            sources:
              github:
                token_env: GITHUB_TOKEN
                owners: [crlough]
          - tenant_id: personal
            display_name: Duplicate
            sources:
              github:
                token_env: GITHUB_TOKEN
                owners: [octocat]
        """,
    )

    with pytest.raises(TenantConfigError, match="Duplicate tenant_id"):
        load_tenant_registry(path)


def test_loader_rejects_missing_github_source(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
        tenants:
          - tenant_id: personal
            display_name: Missing GitHub
            sources: {}
        """,
    )

    with pytest.raises(TenantConfigError, match="must define a github source"):
        load_tenant_registry(path)


def test_loader_rejects_actual_token_where_env_reference_belongs(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
        tenants:
          - tenant_id: personal
            display_name: Secret Mistake
            sources:
              github:
                token_env: ghp_accidentally_committed_token
                owners: [crlough]
        """,
    )

    with pytest.raises(TenantConfigError, match="not a token value"):
        load_tenant_registry(path)


def test_validate_env_var_name_accepts_references_not_secrets() -> None:
    assert validate_env_var_name("GITHUB_TOKEN") == "GITHUB_TOKEN"

    for invalid in ["", "github_token", "ghp_secret", "GITHUB-TOKEN"]:
        with pytest.raises(TenantConfigError):
            validate_env_var_name(invalid)


def test_loader_requires_at_least_one_owner_or_repository(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
        tenants:
          - tenant_id: personal
            display_name: Empty Scope
            sources:
              github:
                token_env: GITHUB_TOKEN
                owners: []
                repositories: []
        """,
    )

    with pytest.raises(TenantConfigError, match="at least one owner or repository"):
        load_tenant_registry(path)


def test_loader_rejects_invalid_repository_shape(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        """
        tenants:
          - tenant_id: personal
            display_name: Bad Repo
            sources:
              github:
                token_env: GITHUB_TOKEN
                repositories: [not-a-full-name]
        """,
    )

    with pytest.raises(TenantConfigError, match="owner/name"):
        load_tenant_registry(path)


def test_tenant_delta_paths_are_tenant_scoped(monkeypatch) -> None:
    monkeypatch.delenv("KABUTO_DATA_ROOT", raising=False)

    assert tenant_delta_root("personal") == PROJECT_ROOT / ".local/data/delta/tenants/personal"
    assert delta_table_path("personal", "bronze", "github", "pull_requests") == (
        PROJECT_ROOT / ".local/data/delta/tenants/personal/bronze/github/pull_requests"
    )
    assert delta_table_path("sandbox", "bronze", "github", "pull_requests") == (
        PROJECT_ROOT / ".local/data/delta/tenants/sandbox/bronze/github/pull_requests"
    )


def test_delta_table_path_rejects_invalid_layer_and_segments() -> None:
    with pytest.raises(ValueError, match="Delta layer"):
        delta_table_path("personal", "raw", "github", "pull_requests")

    with pytest.raises(ValueError, match="single path segment"):
        delta_table_path("personal", "bronze", "github/archive", "pull_requests")

    with pytest.raises(TenantConfigError):
        delta_table_path("bad-tenant", "bronze", "github", "pull_requests")
