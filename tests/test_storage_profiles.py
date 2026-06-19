from __future__ import annotations

from pathlib import Path

import pytest

from kabuto_kurage.paths import (
    PROJECT_ROOT,
    StorageConfigError,
    active_storage_profile,
    delta_root,
    delta_root_uri,
    delta_table_path,
    delta_table_uri,
    duckdb_delta_table_uri,
)

OBJECT_STORE_ENV_VARS = [
    "KABUTO_STORAGE_PROFILE",
    "KABUTO_STORAGE_PREFIX",
    "KABUTO_MINIO_BUCKET",
    "KABUTO_MINIO_ENDPOINT_URL",
    "KABUTO_MINIO_ACCESS_KEY_ID",
    "KABUTO_MINIO_SECRET_ACCESS_KEY",
    "KABUTO_MINIO_REGION",
    "KABUTO_MINIO_ALLOW_HTTP",
    "KABUTO_R2_BUCKET",
    "KABUTO_R2_ACCOUNT_ID",
    "KABUTO_R2_ACCESS_KEY_ID",
    "KABUTO_R2_SECRET_ACCESS_KEY",
    "KABUTO_R2_REGION",
]


def clear_storage_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in OBJECT_STORE_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


def test_local_storage_profile_preserves_existing_default_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_storage_env(monkeypatch)
    monkeypatch.delenv("KABUTO_DATA_ROOT", raising=False)

    profile = active_storage_profile()

    assert profile.name == "local"
    assert profile.local_delta_root == PROJECT_ROOT / ".local" / "data" / "delta"
    assert profile.delta_root_uri == str(PROJECT_ROOT / ".local" / "data" / "delta")
    assert delta_root() == PROJECT_ROOT / ".local" / "data" / "delta"
    assert delta_root_uri() == str(PROJECT_ROOT / ".local" / "data" / "delta")
    assert delta_table_path("personal", "bronze", "github", "pull_requests") == (
        PROJECT_ROOT / ".local/data/delta/tenants/personal/bronze/github/pull_requests"
    )
    assert delta_table_uri("personal", "bronze", "github", "pull_requests") == str(
        PROJECT_ROOT / ".local/data/delta/tenants/personal/bronze/github/pull_requests"
    )
    assert profile.delta_rs_storage_options() == {}
    assert profile.duckdb_secret_sql() == ("INSTALL delta;", "LOAD delta;")


def test_local_storage_profile_respects_data_root_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    clear_storage_env(monkeypatch)
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path / "data-root"))

    assert delta_root() == (tmp_path / "data-root").resolve() / "delta"
    expected_table_path = (
        tmp_path
        / "data-root"
        / "delta"
        / "tenants"
        / "sandbox"
        / "gold"
        / "github"
        / "pr_cycle_time"
    )
    assert delta_table_path("sandbox", "gold", "github", "pr_cycle_time") == (
        expected_table_path.resolve()
    )


def test_minio_storage_profile_resolves_s3_locations_without_secret_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_storage_env(monkeypatch)
    monkeypatch.setenv("KABUTO_STORAGE_PROFILE", "minio")
    monkeypatch.setenv("KABUTO_STORAGE_PREFIX", "portfolio/kabuto")
    monkeypatch.setenv("KABUTO_MINIO_BUCKET", "kabuto-dev")
    monkeypatch.setenv("KABUTO_MINIO_ENDPOINT_URL", "http://localhost:9000")
    monkeypatch.setenv("KABUTO_MINIO_ACCESS_KEY_ID", "minio-access-key")
    monkeypatch.setenv("KABUTO_MINIO_SECRET_ACCESS_KEY", "minio-secret-value")

    profile = active_storage_profile()

    assert profile.name == "minio"
    assert profile.local_delta_root is None
    assert delta_root_uri() == "s3://kabuto-dev/portfolio/kabuto/delta"
    assert delta_table_uri("sandbox", "silver", "github", "repositories") == (
        "s3://kabuto-dev/portfolio/kabuto/delta/tenants/sandbox/silver/github/repositories"
    )
    assert duckdb_delta_table_uri("sandbox", "silver", "github", "repositories") == (
        "s3://kabuto-dev/portfolio/kabuto/delta/tenants/sandbox/silver/github/repositories"
    )

    safe_options = profile.delta_rs_storage_options()
    safe_sql = "\n".join(profile.duckdb_secret_sql())
    assert safe_options["AWS_ACCESS_KEY_ID"] == "<KABUTO_MINIO_ACCESS_KEY_ID>"
    assert safe_options["AWS_SECRET_ACCESS_KEY"] == "<KABUTO_MINIO_SECRET_ACCESS_KEY>"
    assert "minio-secret-value" not in str(profile.safe_summary())
    assert "minio-secret-value" not in str(safe_options)
    assert "minio-secret-value" not in safe_sql
    assert "KABUTO_MINIO_SECRET_ACCESS_KEY" in safe_sql

    secret_options = profile.delta_rs_storage_options(include_secrets=True)
    assert secret_options["AWS_ACCESS_KEY_ID"] == "minio-access-key"
    assert secret_options["AWS_SECRET_ACCESS_KEY"] == "minio-secret-value"

    with pytest.raises(StorageConfigError, match="local filesystem Delta path"):
        delta_table_path("sandbox", "silver", "github", "repositories")


def test_r2_storage_profile_resolves_delta_and_duckdb_locations_without_secret_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_storage_env(monkeypatch)
    monkeypatch.setenv("KABUTO_STORAGE_PROFILE", "r2")
    monkeypatch.setenv("KABUTO_STORAGE_PREFIX", "portfolio/kabuto")
    monkeypatch.setenv("KABUTO_R2_BUCKET", "kabuto-r2")
    monkeypatch.setenv("KABUTO_R2_ACCOUNT_ID", "account-id-from-env")
    monkeypatch.setenv("KABUTO_R2_ACCESS_KEY_ID", "r2-access-key")
    monkeypatch.setenv("KABUTO_R2_SECRET_ACCESS_KEY", "r2-secret-value")

    profile = active_storage_profile()

    assert profile.name == "r2"
    assert delta_root_uri() == "s3://kabuto-r2/portfolio/kabuto/delta"
    assert delta_table_uri("sandbox", "gold", "github", "pr_cycle_time") == (
        "s3://kabuto-r2/portfolio/kabuto/delta/tenants/sandbox/gold/github/pr_cycle_time"
    )
    assert duckdb_delta_table_uri("sandbox", "gold", "github", "pr_cycle_time") == (
        "r2://kabuto-r2/portfolio/kabuto/delta/tenants/sandbox/gold/github/pr_cycle_time"
    )

    safe_summary = profile.safe_summary()
    safe_options = profile.delta_rs_storage_options()
    safe_sql = "\n".join(profile.duckdb_secret_sql())
    assert safe_summary["endpoint_url"] == "https://account-id-from-env.r2.cloudflarestorage.com"
    assert safe_summary["account_id_env"] == "KABUTO_R2_ACCOUNT_ID"
    assert "r2-secret-value" not in str(safe_summary)
    assert "r2-secret-value" not in str(safe_options)
    assert "r2-secret-value" not in safe_sql
    assert "<KABUTO_R2_SECRET_ACCESS_KEY>" in safe_sql

    secret_options = profile.delta_rs_storage_options(include_secrets=True)
    assert secret_options["AWS_ACCESS_KEY_ID"] == "r2-access-key"
    assert secret_options["AWS_SECRET_ACCESS_KEY"] == "r2-secret-value"
    assert secret_options["AWS_ENDPOINT_URL"] == (
        "https://account-id-from-env.r2.cloudflarestorage.com"
    )


def test_storage_profile_validation_rejects_bad_profile_missing_bucket_and_bad_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_storage_env(monkeypatch)
    monkeypatch.setenv("KABUTO_STORAGE_PROFILE", "ftp")
    with pytest.raises(StorageConfigError, match="KABUTO_STORAGE_PROFILE"):
        active_storage_profile()

    monkeypatch.setenv("KABUTO_STORAGE_PROFILE", "minio")
    with pytest.raises(StorageConfigError, match="KABUTO_MINIO_BUCKET"):
        active_storage_profile()

    monkeypatch.setenv("KABUTO_MINIO_BUCKET", "kabuto-dev")
    monkeypatch.setenv("KABUTO_STORAGE_PREFIX", "../bad")
    with pytest.raises(StorageConfigError, match="KABUTO_STORAGE_PREFIX"):
        active_storage_profile()
