"""Tenant and source configuration for the local portfolio platform.

The project models multi-tenancy explicitly even while running locally. Config files
contain tenant IDs, source scopes, and secret *references* such as environment-variable
names. They must never contain GitHub token values.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from kabuto_kurage.paths import PROJECT_ROOT

TENANT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,62}$")
ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]{1,127}$")
GITHUB_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GITHUB_TOKEN_PREFIXES = ("ghp_", "github_pat_", "gho_", "ghu_", "ghs_", "ghr_")

DEFAULT_TENANT_CONFIG_PATH = PROJECT_ROOT / "config" / "tenants.example.yaml"


class TenantConfigError(ValueError):
    """Raised when tenant/source configuration is missing or invalid."""


@dataclass(frozen=True)
class GitHubSourceConfig:
    """GitHub source settings for one tenant.

    `token_env` is an environment-variable name, not a token value.
    """

    token_env: str
    api_base_url: str
    owners: tuple[str, ...]
    repositories: tuple[str, ...]


@dataclass(frozen=True)
class TenantConfig:
    """Configuration for one tenant."""

    tenant_id: str
    display_name: str
    github: GitHubSourceConfig


@dataclass(frozen=True)
class TenantRegistry:
    """Validated tenant registry keyed by tenant ID."""

    tenants: dict[str, TenantConfig]

    def get(self, tenant_id: str) -> TenantConfig:
        """Return a tenant by ID after validating the lookup key."""

        validate_tenant_id(tenant_id)
        try:
            return self.tenants[tenant_id]
        except KeyError as exc:
            raise TenantConfigError(f"Unknown tenant_id: {tenant_id}") from exc

    @property
    def tenant_ids(self) -> tuple[str, ...]:
        """Return configured tenant IDs in deterministic order."""

        return tuple(sorted(self.tenants))


def validate_tenant_id(tenant_id: str) -> str:
    """Validate and return a tenant ID safe for logical scoping and paths."""

    if not isinstance(tenant_id, str) or not tenant_id:
        raise TenantConfigError("tenant_id is required")
    if not TENANT_ID_PATTERN.fullmatch(tenant_id):
        raise TenantConfigError(
            "tenant_id must be 3-63 chars, start with a lowercase letter, and contain "
            "only lowercase letters, digits, and underscores"
        )
    return tenant_id


def validate_env_var_name(name: str) -> str:
    """Validate that a value is an env-var reference rather than a secret."""

    if not isinstance(name, str) or not name:
        raise TenantConfigError("token_env is required for GitHub sources")
    if name.lower().startswith(GITHUB_TOKEN_PREFIXES):
        raise TenantConfigError("token_env must be an environment-variable name, not a token value")
    if not ENV_VAR_PATTERN.fullmatch(name):
        raise TenantConfigError(
            "token_env must be an uppercase environment-variable name such as GITHUB_TOKEN"
        )
    return name


def tenant_config_path() -> Path:
    """Return the configured tenant YAML path, defaulting to the committed example."""

    configured = os.environ.get("KABUTO_TENANTS_CONFIG")
    if configured:
        return Path(configured).expanduser().resolve()
    return DEFAULT_TENANT_CONFIG_PATH


def load_tenant_registry(path: Path | None = None) -> TenantRegistry:
    """Load and validate tenant/source configuration from YAML."""

    config_path = path or tenant_config_path()
    with config_path.open("r", encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file) or {}

    if not isinstance(raw, dict):
        raise TenantConfigError("Tenant config root must be a mapping")

    raw_tenants = raw.get("tenants")
    if not isinstance(raw_tenants, list) or not raw_tenants:
        raise TenantConfigError("Tenant config must contain a non-empty tenants list")

    tenants: dict[str, TenantConfig] = {}
    for index, raw_tenant in enumerate(raw_tenants):
        tenant = _parse_tenant(raw_tenant, index)
        if tenant.tenant_id in tenants:
            raise TenantConfigError(f"Duplicate tenant_id: {tenant.tenant_id}")
        tenants[tenant.tenant_id] = tenant

    return TenantRegistry(tenants=tenants)


def _parse_tenant(raw_tenant: Any, index: int) -> TenantConfig:
    if not isinstance(raw_tenant, dict):
        raise TenantConfigError(f"Tenant entry at index {index} must be a mapping")

    tenant_id = validate_tenant_id(_required_string(raw_tenant, "tenant_id"))
    display_name = _required_string(raw_tenant, "display_name")

    sources = raw_tenant.get("sources")
    if not isinstance(sources, dict):
        raise TenantConfigError(f"Tenant {tenant_id} must define sources")

    github_source = sources.get("github")
    if not isinstance(github_source, dict):
        raise TenantConfigError(f"Tenant {tenant_id} must define a github source")

    return TenantConfig(
        tenant_id=tenant_id,
        display_name=display_name,
        github=_parse_github_source(github_source, tenant_id),
    )


def _parse_github_source(raw_source: dict[str, Any], tenant_id: str) -> GitHubSourceConfig:
    token_env = validate_env_var_name(_required_string(raw_source, "token_env"))
    api_base_url = raw_source.get("api_base_url", "https://api.github.com")
    if not isinstance(api_base_url, str) or not api_base_url.startswith("https://"):
        raise TenantConfigError(f"Tenant {tenant_id} GitHub api_base_url must be an https URL")

    owners = _string_tuple(raw_source.get("owners", []), field="owners", tenant_id=tenant_id)
    repositories = _string_tuple(
        raw_source.get("repositories", []), field="repositories", tenant_id=tenant_id
    )
    for repository in repositories:
        if not GITHUB_REPOSITORY_PATTERN.fullmatch(repository):
            raise TenantConfigError(
                f"Tenant {tenant_id} GitHub repository must be owner/name: {repository}"
            )

    if not owners and not repositories:
        raise TenantConfigError(
            f"Tenant {tenant_id} GitHub source must include at least one owner or repository"
        )

    return GitHubSourceConfig(
        token_env=token_env,
        api_base_url=api_base_url,
        owners=owners,
        repositories=repositories,
    )


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise TenantConfigError(f"{key} is required")
    return value


def _string_tuple(value: Any, *, field: str, tenant_id: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TenantConfigError(f"Tenant {tenant_id} field {field} must be a list")
    if not all(isinstance(item, str) and item for item in value):
        raise TenantConfigError(f"Tenant {tenant_id} field {field} must contain only strings")
    return tuple(value)
