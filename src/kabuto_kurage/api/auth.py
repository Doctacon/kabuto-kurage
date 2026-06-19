"""Local bearer-token authorization for the export REST API.

The API intentionally keeps authentication simple for a local portfolio project: each
bearer token maps to an explicit allowlist of tenant IDs. Token values are supplied
through environment variables or ignored local config, not committed project files.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hmac import compare_digest
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from kabuto_kurage.tenancy import validate_tenant_id

API_TOKENS_JSON_ENV = "KABUTO_API_TOKENS_JSON"
API_TOKENS_CONFIG_ENV = "KABUTO_API_TOKENS_CONFIG"


class APIAuthConfigError(ValueError):
    """Raised when local API token configuration is malformed."""


class APIAuthError(PermissionError):
    """Raised when bearer token authentication fails."""


class TenantAccessDeniedError(PermissionError):
    """Raised when a valid token is not allowed to access a tenant."""


@dataclass(frozen=True)
class APIPrincipal:
    """Authenticated local API principal.

    The token value itself is intentionally not retained on the principal so it cannot
    accidentally appear in API responses or logs generated from this object.
    """

    allowed_tenant_ids: frozenset[str]

    def can_access(self, tenant_id: str) -> bool:
        """Return whether this principal can access the requested tenant."""

        return tenant_id in self.allowed_tenant_ids


@dataclass(frozen=True)
class APITokenRegistry:
    """Local token registry keyed by bearer token value."""

    token_allowlists: Mapping[str, frozenset[str]]

    def authenticate(self, token: str) -> APIPrincipal:
        """Return a principal for a bearer token or raise an auth error."""

        if not token:
            raise APIAuthError("Missing bearer token")
        for configured_token, allowed_tenant_ids in self.token_allowlists.items():
            if compare_digest(token, configured_token):
                return APIPrincipal(allowed_tenant_ids=allowed_tenant_ids)
        raise APIAuthError("Invalid bearer token")


def load_api_token_registry() -> APITokenRegistry:
    """Load local API token allowlists from environment-derived settings.

    Supported formats:

    - ``KABUTO_API_TOKENS_JSON`` as a JSON object mapping token values to tenant ID lists.
    - ``KABUTO_API_TOKENS_CONFIG`` as a YAML/JSON path containing ``tokens`` entries with
      ``token_env`` and ``tenant_ids``. The actual token values are read from those env vars.

    If neither setting is present, an empty registry is returned and all bearer tokens are
    treated as invalid.
    """

    tokens_json = os.environ.get(API_TOKENS_JSON_ENV)
    if tokens_json:
        return APITokenRegistry(token_allowlists=_parse_token_mapping_json(tokens_json))

    config_path = os.environ.get(API_TOKENS_CONFIG_ENV)
    if config_path:
        return APITokenRegistry(token_allowlists=_load_token_config_path(Path(config_path)))

    return APITokenRegistry(token_allowlists={})


def require_tenant_access(tenant_id: str, authorization_header: str | None) -> APIPrincipal:
    """Authenticate a bearer token and authorize it for one tenant."""

    safe_tenant_id = validate_tenant_id(tenant_id)
    token = _parse_bearer_token(authorization_header)
    principal = load_api_token_registry().authenticate(token)
    if not principal.can_access(safe_tenant_id):
        raise TenantAccessDeniedError(f"Token is not allowed to access tenant {safe_tenant_id}")
    return principal


def _parse_bearer_token(authorization_header: str | None) -> str:
    if authorization_header is None or not authorization_header.strip():
        raise APIAuthError("Missing Authorization bearer token")

    parts = authorization_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise APIAuthError("Authorization header must use Bearer authentication")
    return parts[1]


def _parse_token_mapping_json(raw_json: str) -> dict[str, frozenset[str]]:
    try:
        raw = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise APIAuthConfigError(f"{API_TOKENS_JSON_ENV} must contain valid JSON") from exc
    if not isinstance(raw, dict):
        raise APIAuthConfigError(f"{API_TOKENS_JSON_ENV} must be a JSON object")
    return _normalize_token_mapping(raw)


def _load_token_config_path(config_path: Path) -> dict[str, frozenset[str]]:
    resolved_path = config_path.expanduser().resolve()
    with resolved_path.open("r", encoding="utf-8") as config_file:
        if resolved_path.suffix.lower() == ".json":
            raw = json.load(config_file)
        else:
            raw = yaml.safe_load(config_file) or {}
    if not isinstance(raw, dict):
        raise APIAuthConfigError("API token config root must be a mapping")

    raw_tokens = raw.get("tokens")
    if not isinstance(raw_tokens, list):
        raise APIAuthConfigError("API token config must contain a tokens list")

    token_allowlists: dict[str, frozenset[str]] = {}
    for index, raw_entry in enumerate(raw_tokens):
        if not isinstance(raw_entry, dict):
            raise APIAuthConfigError(f"API token entry {index} must be a mapping")
        token_env = raw_entry.get("token_env")
        if not isinstance(token_env, str) or not token_env:
            raise APIAuthConfigError(f"API token entry {index} must define token_env")
        token_value = os.environ.get(token_env)
        if not token_value:
            raise APIAuthConfigError(f"Environment variable {token_env} is required")
        token_allowlists[token_value] = _normalize_tenant_ids(raw_entry.get("tenant_ids"))
    return token_allowlists


def _normalize_token_mapping(raw: Mapping[str, object]) -> dict[str, frozenset[str]]:
    token_allowlists: dict[str, frozenset[str]] = {}
    for raw_token, raw_tenant_ids in raw.items():
        if not isinstance(raw_token, str) or not raw_token:
            raise APIAuthConfigError("API token values must be non-empty strings")
        token_allowlists[raw_token] = _normalize_tenant_ids(raw_tenant_ids)
    return token_allowlists


def _normalize_tenant_ids(raw_tenant_ids: object) -> frozenset[str]:
    if not isinstance(raw_tenant_ids, Sequence) or isinstance(
        raw_tenant_ids, str | bytes | bytearray
    ):
        raise APIAuthConfigError("API token tenant allowlists must be lists of tenant IDs")
    tenant_ids = tuple(raw_tenant_ids)
    if not tenant_ids:
        raise APIAuthConfigError("API token tenant allowlists must not be empty")
    if not all(isinstance(tenant_id, str) for tenant_id in tenant_ids):
        raise APIAuthConfigError("API token tenant allowlists must contain only strings")
    return frozenset(validate_tenant_id(tenant_id) for tenant_id in tenant_ids)
