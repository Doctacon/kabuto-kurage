"""Shared storage paths and URIs for the portfolio data platform.

Runtime data stays under ignored local directories by default. Tenant-scoped Delta paths
make the local multi-tenancy model visible while storage profiles let the same logical
layout target local files, MinIO, or Cloudflare R2.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DELTA_LAYERS = ("bronze", "silver", "gold")
STORAGE_PROFILES = ("local", "minio", "r2")
DEFAULT_STORAGE_PREFIX = "kabuto-kurage"

StorageProfileName = Literal["local", "minio", "r2"]


class StorageConfigError(ValueError):
    """Raised when storage profile configuration is missing or invalid."""


@dataclass(frozen=True)
class DeltaStorageProfile:
    """Resolved storage settings for Delta table locations and engine options.

    Secret-bearing values are loaded only when explicitly requested through
    ``delta_rs_storage_options(include_secrets=True)`` or
    ``duckdb_secret_sql(include_secrets=True)``. The default representation uses
    environment-variable placeholders so docs/tests can reason about required settings
    without leaking local credentials.
    """

    name: StorageProfileName
    delta_root_uri: str
    local_delta_root: Path | None
    bucket: str | None = None
    prefix: str = DEFAULT_STORAGE_PREFIX
    endpoint_url: str | None = None
    region: str | None = None
    account_id: str | None = None
    allow_http: bool = False

    @property
    def is_local(self) -> bool:
        """Return whether this profile points at local filesystem storage."""

        return self.name == "local"

    def delta_table_uri(self, tenant_id: str, layer: str, source: str, table_name: str) -> str:
        """Return the Delta table URI for one tenant/source/table on this profile."""

        relative = _tenant_table_relative_path(tenant_id, layer, source, table_name)
        return _join_uri(self.delta_root_uri, relative)

    def delta_table_path(self, tenant_id: str, layer: str, source: str, table_name: str) -> Path:
        """Return a local filesystem Delta table path for local profiles only."""

        if self.local_delta_root is None:
            raise StorageConfigError(
                f"Storage profile {self.name!r} does not have a local filesystem Delta path; "
                "use delta_table_uri() for object-storage profiles"
            )
        relative = _tenant_table_relative_path(tenant_id, layer, source, table_name)
        return self.local_delta_root / relative

    def duckdb_delta_table_uri(
        self, tenant_id: str, layer: str, source: str, table_name: str
    ) -> str:
        """Return the URI DuckDB should use for ``delta_scan``.

        Cloudflare R2 can be addressed by DuckDB's `r2://` scheme when a `TYPE r2`
        secret is configured; delta-rs still uses the S3-compatible `s3://` URI plus
        endpoint storage options.
        """

        if self.name != "r2":
            return self.delta_table_uri(tenant_id, layer, source, table_name)
        if self.bucket is None:
            raise StorageConfigError("R2 profile requires KABUTO_R2_BUCKET")
        relative = _tenant_table_relative_path(tenant_id, layer, source, table_name)
        prefix = _normalize_prefix(self.prefix)
        return _join_uri(f"r2://{self.bucket}", f"{prefix}/delta/{relative}")

    def delta_rs_storage_options(self, *, include_secrets: bool = False) -> dict[str, str]:
        """Return storage options suitable for delta-rs/deltalake.

        By default, secret values are represented by environment-variable placeholders.
        Pass ``include_secrets=True`` only at the storage-engine boundary.
        """

        if self.name == "local":
            return {}
        if self.name == "minio":
            return _minio_delta_rs_storage_options(include_secrets=include_secrets)
        if self.name == "r2":
            return _r2_delta_rs_storage_options(include_secrets=include_secrets)
        raise StorageConfigError(f"Unsupported storage profile: {self.name}")

    def duckdb_secret_sql(self, *, include_secrets: bool = False) -> tuple[str, ...]:
        """Return DuckDB extension/secret statements for this profile.

        The default output is safe for docs/evidence because secret values are placeholders
        named after environment variables, not actual credentials.
        """

        if self.name == "local":
            return ("INSTALL delta;", "LOAD delta;")
        if self.name == "minio":
            access_key = _secret_value(
                "KABUTO_MINIO_ACCESS_KEY_ID", include_secrets=include_secrets
            )
            secret_key = _secret_value(
                "KABUTO_MINIO_SECRET_ACCESS_KEY", include_secrets=include_secrets
            )
            endpoint = _minio_endpoint_url().removeprefix("http://").removeprefix("https://")
            use_ssl = "false" if _minio_allow_http() else "true"
            region = os.environ.get("KABUTO_MINIO_REGION", "us-east-1")
            return (
                "INSTALL httpfs;",
                "LOAD httpfs;",
                "INSTALL delta;",
                "LOAD delta;",
                "CREATE OR REPLACE SECRET kabuto_minio ("
                "TYPE s3, "
                f"KEY_ID '{access_key}', "
                f"SECRET '{secret_key}', "
                f"ENDPOINT '{endpoint}', "
                f"REGION '{region}', "
                "URL_STYLE 'path', "
                f"USE_SSL {use_ssl}"
                ");",
            )
        if self.name == "r2":
            access_key = _secret_value("KABUTO_R2_ACCESS_KEY_ID", include_secrets=include_secrets)
            secret_key = _secret_value(
                "KABUTO_R2_SECRET_ACCESS_KEY", include_secrets=include_secrets
            )
            account_id = _secret_value("KABUTO_R2_ACCOUNT_ID", include_secrets=include_secrets)
            return (
                "INSTALL httpfs;",
                "LOAD httpfs;",
                "INSTALL delta;",
                "LOAD delta;",
                "CREATE OR REPLACE SECRET kabuto_r2 ("
                "TYPE r2, "
                f"KEY_ID '{access_key}', "
                f"SECRET '{secret_key}', "
                f"ACCOUNT_ID '{account_id}'"
                ");",
            )
        raise StorageConfigError(f"Unsupported storage profile: {self.name}")

    def safe_summary(self) -> dict[str, str | bool | None]:
        """Return non-secret profile details for logging/docs/debugging."""

        return {
            "name": self.name,
            "delta_root_uri": self.delta_root_uri,
            "local_delta_root": str(self.local_delta_root) if self.local_delta_root else None,
            "bucket": self.bucket,
            "prefix": self.prefix,
            "endpoint_url": self.endpoint_url,
            "region": self.region,
            "account_id_env": "KABUTO_R2_ACCOUNT_ID" if self.name == "r2" else None,
            "allow_http": self.allow_http,
        }


def data_root() -> Path:
    """Return the local root directory for generated runtime data."""

    configured = os.environ.get("KABUTO_DATA_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return PROJECT_ROOT / ".local" / "data"


def storage_profile_name() -> StorageProfileName:
    """Return the active storage profile name, defaulting to local filesystem."""

    configured = os.environ.get("KABUTO_STORAGE_PROFILE", "local").strip().lower()
    if configured not in STORAGE_PROFILES:
        raise StorageConfigError(
            f"KABUTO_STORAGE_PROFILE must be one of {STORAGE_PROFILES}: {configured}"
        )
    return configured  # type: ignore[return-value]


def active_storage_profile() -> DeltaStorageProfile:
    """Return the active Delta storage profile from environment configuration."""

    profile_name = storage_profile_name()
    if profile_name == "local":
        local_root = data_root() / "delta"
        return DeltaStorageProfile(
            name="local",
            delta_root_uri=str(local_root),
            local_delta_root=local_root,
        )
    if profile_name == "minio":
        bucket = _required_env("KABUTO_MINIO_BUCKET", profile="minio")
        prefix = _storage_prefix()
        endpoint_url = _minio_endpoint_url()
        region = os.environ.get("KABUTO_MINIO_REGION", "us-east-1")
        return DeltaStorageProfile(
            name="minio",
            delta_root_uri=_join_uri(f"s3://{bucket}", f"{prefix}/delta"),
            local_delta_root=None,
            bucket=bucket,
            prefix=prefix,
            endpoint_url=endpoint_url,
            region=region,
            allow_http=_minio_allow_http(),
        )
    if profile_name == "r2":
        bucket = _required_env("KABUTO_R2_BUCKET", profile="r2")
        account_id = _required_env("KABUTO_R2_ACCOUNT_ID", profile="r2")
        prefix = _storage_prefix()
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        return DeltaStorageProfile(
            name="r2",
            delta_root_uri=_join_uri(f"s3://{bucket}", f"{prefix}/delta"),
            local_delta_root=None,
            bucket=bucket,
            prefix=prefix,
            endpoint_url=endpoint_url,
            region=os.environ.get("KABUTO_R2_REGION", "auto"),
            account_id=account_id,
        )
    raise StorageConfigError(f"Unsupported storage profile: {profile_name}")


def delta_root() -> Path:
    """Return the local Delta root path.

    This compatibility helper is valid only for the local storage profile. Object-store
    profiles should use ``delta_root_uri()`` instead.
    """

    profile = active_storage_profile()
    if profile.local_delta_root is None:
        raise StorageConfigError(
            f"Storage profile {profile.name!r} does not have a local Delta root; "
            "use delta_root_uri() for object-storage profiles"
        )
    return profile.local_delta_root


def delta_root_uri() -> str:
    """Return the active Delta root URI for local or object-storage profiles."""

    return active_storage_profile().delta_root_uri


def tenant_delta_root(tenant_id: str) -> Path:
    """Return the local root Delta path for one tenant."""

    from kabuto_kurage.tenancy import validate_tenant_id

    profile = active_storage_profile()
    if profile.local_delta_root is None:
        raise StorageConfigError(
            f"Storage profile {profile.name!r} does not have local tenant Delta paths; "
            "use tenant_delta_root_uri() for object-storage profiles"
        )
    return profile.local_delta_root / "tenants" / validate_tenant_id(tenant_id)


def tenant_delta_root_uri(tenant_id: str) -> str:
    """Return the active Delta root URI for one tenant."""

    from kabuto_kurage.tenancy import validate_tenant_id

    return _join_uri(delta_root_uri(), f"tenants/{validate_tenant_id(tenant_id)}")


def delta_layer_root(tenant_id: str, layer: str) -> Path:
    """Return the local Delta path for one tenant and lakehouse layer."""

    if layer not in DELTA_LAYERS:
        raise ValueError(f"Delta layer must be one of {DELTA_LAYERS}: {layer}")
    return tenant_delta_root(tenant_id) / layer


def delta_layer_root_uri(tenant_id: str, layer: str) -> str:
    """Return the active Delta URI for one tenant and lakehouse layer."""

    if layer not in DELTA_LAYERS:
        raise ValueError(f"Delta layer must be one of {DELTA_LAYERS}: {layer}")
    return _join_uri(tenant_delta_root_uri(tenant_id), layer)


def delta_table_path(tenant_id: str, layer: str, source: str, table_name: str) -> Path:
    """Return the local Delta table path for tenant/source/table data.

    Shape: `.local/data/delta/tenants/{tenant_id}/{layer}/{source}/{table_name}`.
    Object-storage profiles should use ``delta_table_uri()``.
    """

    return active_storage_profile().delta_table_path(tenant_id, layer, source, table_name)


def delta_table_uri(tenant_id: str, layer: str, source: str, table_name: str) -> str:
    """Return the active Delta table URI for tenant/source/table data."""

    return active_storage_profile().delta_table_uri(tenant_id, layer, source, table_name)


def duckdb_delta_table_uri(tenant_id: str, layer: str, source: str, table_name: str) -> str:
    """Return the URI DuckDB should use to scan an active-profile Delta table."""

    return active_storage_profile().duckdb_delta_table_uri(tenant_id, layer, source, table_name)


def _tenant_table_relative_path(tenant_id: str, layer: str, source: str, table_name: str) -> Path:
    from kabuto_kurage.tenancy import validate_tenant_id

    if layer not in DELTA_LAYERS:
        raise ValueError(f"Delta layer must be one of {DELTA_LAYERS}: {layer}")
    _validate_path_segment(source, field="source")
    _validate_path_segment(table_name, field="table_name")
    return Path("tenants") / validate_tenant_id(tenant_id) / layer / source / table_name


def _validate_path_segment(value: str, *, field: str) -> str:
    if not value or "/" in value or value in {".", ".."}:
        raise ValueError(f"{field} must be a non-empty single path segment")
    return value


def _join_uri(root: str, relative: str | Path) -> str:
    clean_root = root.rstrip("/")
    clean_relative = str(relative).strip("/")
    return f"{clean_root}/{clean_relative}" if clean_relative else clean_root


def _storage_prefix() -> str:
    return _normalize_prefix(os.environ.get("KABUTO_STORAGE_PREFIX", DEFAULT_STORAGE_PREFIX))


def _normalize_prefix(prefix: str) -> str:
    clean_prefix = prefix.strip().strip("/")
    has_parent_or_current_part = any(part in {".", ".."} for part in clean_prefix.split("/"))
    if not clean_prefix or "//" in clean_prefix or has_parent_or_current_part:
        raise StorageConfigError("KABUTO_STORAGE_PREFIX must be a non-empty relative path")
    return clean_prefix


def _required_env(name: str, *, profile: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise StorageConfigError(f"{name} is required for {profile} storage profile")
    return value


def _secret_value(name: str, *, include_secrets: bool) -> str:
    if not include_secrets:
        return f"<{name}>"
    return _required_env(name, profile="object-store")


def _minio_endpoint_url() -> str:
    return os.environ.get("KABUTO_MINIO_ENDPOINT_URL", "http://localhost:9000")


def _minio_allow_http() -> bool:
    value = os.environ.get("KABUTO_MINIO_ALLOW_HTTP", "true").strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise StorageConfigError("KABUTO_MINIO_ALLOW_HTTP must be a boolean value")


def _minio_delta_rs_storage_options(*, include_secrets: bool) -> dict[str, str]:
    endpoint_url = _minio_endpoint_url()
    options = {
        "AWS_ACCESS_KEY_ID": _secret_value(
            "KABUTO_MINIO_ACCESS_KEY_ID", include_secrets=include_secrets
        ),
        "AWS_SECRET_ACCESS_KEY": _secret_value(
            "KABUTO_MINIO_SECRET_ACCESS_KEY", include_secrets=include_secrets
        ),
        "AWS_ENDPOINT_URL": endpoint_url,
        "AWS_REGION": os.environ.get("KABUTO_MINIO_REGION", "us-east-1"),
        "aws_conditional_put": "etag",
    }
    if _minio_allow_http():
        options["allow_http"] = "true"
    return options


def _r2_delta_rs_storage_options(*, include_secrets: bool) -> dict[str, str]:
    account_id = _secret_value("KABUTO_R2_ACCOUNT_ID", include_secrets=include_secrets)
    endpoint_url = (
        f"https://{account_id}.r2.cloudflarestorage.com"
        if include_secrets
        else "https://<KABUTO_R2_ACCOUNT_ID>.r2.cloudflarestorage.com"
    )
    return {
        "AWS_ACCESS_KEY_ID": _secret_value(
            "KABUTO_R2_ACCESS_KEY_ID", include_secrets=include_secrets
        ),
        "AWS_SECRET_ACCESS_KEY": _secret_value(
            "KABUTO_R2_SECRET_ACCESS_KEY", include_secrets=include_secrets
        ),
        "AWS_ENDPOINT_URL": endpoint_url,
        "AWS_REGION": os.environ.get("KABUTO_R2_REGION", "auto"),
        "aws_conditional_put": "etag",
    }
