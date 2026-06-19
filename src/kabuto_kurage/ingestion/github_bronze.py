"""dlt-native GitHub ingestion into tenant-scoped bronze Delta tables.

This module defines explicit dlt source/resources for GitHub repositories and pull
requests while keeping pagination, rate-limit headers, raw payloads, dlt schema/state
artifacts, and Delta write semantics visible for learning.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

import dlt
import jwt
import pyarrow as pa
import requests
from deltalake import DeltaTable, write_deltalake
from dlt.extract.source import DltSource
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth
from dlt.sources.helpers.rest_client.client import RESTClient
from dlt.sources.helpers.rest_client.paginators import HeaderLinkPaginator

from kabuto_kurage.paths import data_root, delta_table_path
from kabuto_kurage.tenancy import GitHubSourceConfig, TenantConfig, load_tenant_registry

GITHUB_API_VERSION = "2022-11-28"
GITHUB_SOURCE = "github"
REPOSITORY_RESOURCE = "repositories"
PULL_REQUEST_RESOURCE = "pull_requests"
DEFAULT_USER_AGENT = "kabuto-kurage-github-bronze-ingestion"
DLT_BRONZE_SOURCE_NAME = "github_bronze"
DLT_ARTIFACT_SCHEMA_VERSION = 1
GITHUB_FIXTURE_MODE_ENV = "KABUTO_GITHUB_FIXTURE_MODE"
GITHUB_INCREMENTAL_ENABLED_ENV = "KABUTO_GITHUB_INCREMENTAL_ENABLED"
GITHUB_INCREMENTAL_LOOKBACK_DAYS_ENV = "KABUTO_GITHUB_INCREMENTAL_LOOKBACK_DAYS"
GITHUB_APP_ID_ENV = "GITHUB_APP_ID"
GITHUB_APP_INSTALLATION_ID_ENV = "GITHUB_APP_INSTALLATION_ID"
GITHUB_APP_PRIVATE_KEY_ENV = "GITHUB_APP_PRIVATE_KEY"
GITHUB_APP_PRIVATE_KEY_PATH_ENV = "GITHUB_APP_PRIVATE_KEY_PATH"
GITHUB_AUTH_MODE_ENV = "KABUTO_GITHUB_AUTH_MODE"

BRONZE_SCHEMA = pa.schema(
    [
        ("tenant_id", pa.string()),
        ("source", pa.string()),
        ("resource_type", pa.string()),
        ("fetched_at", pa.timestamp("us", tz="UTC")),
        ("source_id", pa.string()),
        ("source_owner", pa.string()),
        ("source_repo", pa.string()),
        ("source_url", pa.string()),
        ("api_url", pa.string()),
        ("ingestion_run_id", pa.string()),
        ("payload_json", pa.string()),
        ("rate_limit_json", pa.string()),
    ]
)

DLT_BRONZE_COLUMNS: dict[str, dict[str, str]] = {
    "tenant_id": {"data_type": "text"},
    "source": {"data_type": "text"},
    "resource_type": {"data_type": "text"},
    "fetched_at": {"data_type": "timestamp"},
    "source_id": {"data_type": "text"},
    "source_owner": {"data_type": "text"},
    "source_repo": {"data_type": "text"},
    "source_url": {"data_type": "text"},
    "api_url": {"data_type": "text"},
    "ingestion_run_id": {"data_type": "text"},
    "payload_json": {"data_type": "text"},
    "rate_limit_json": {"data_type": "text"},
}


class GitHubIngestionError(RuntimeError):
    """Raised when GitHub bronze ingestion cannot complete safely."""


@dataclass(frozen=True)
class RateLimitSnapshot:
    """Rate-limit information captured from a GitHub API response."""

    limit: int | None
    remaining: int | None
    used: int | None
    reset_epoch_seconds: int | None
    resource: str | None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> RateLimitSnapshot:
        """Build a rate-limit snapshot from response headers when present."""

        return cls(
            limit=_optional_int(headers.get("x-ratelimit-limit")),
            remaining=_optional_int(headers.get("x-ratelimit-remaining")),
            used=_optional_int(headers.get("x-ratelimit-used")),
            reset_epoch_seconds=_optional_int(headers.get("x-ratelimit-reset")),
            resource=headers.get("x-ratelimit-resource"),
        )

    def to_json(self) -> str:
        """Return stable JSON for storage in bronze records."""

        return json.dumps(
            {
                "limit": self.limit,
                "remaining": self.remaining,
                "used": self.used,
                "reset_epoch_seconds": self.reset_epoch_seconds,
                "resource": self.resource,
            },
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True)
class BronzeWriteResult:
    """Summary for one bronze table write."""

    resource_type: str
    table_path: Path
    row_count: int


@dataclass(frozen=True)
class DltArtifactResult:
    """Local paths for dlt schema/state artifacts captured during ingestion."""

    source_name: str
    resource_names: tuple[str, ...]
    schema_path: Path
    state_path: Path

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly artifact summary without secret-bearing values."""

        return {
            "source_name": self.source_name,
            "resource_names": list(self.resource_names),
            "schema_path": str(self.schema_path),
            "state_path": str(self.state_path),
        }


@dataclass(frozen=True)
class GitHubBronzeIngestionResult:
    """Summary for a tenant GitHub bronze ingestion run."""

    tenant_id: str
    ingestion_run_id: str
    fetched_at: datetime
    repository_count: int
    pull_request_count: int
    writes: tuple[BronzeWriteResult, ...]
    rate_limits: tuple[RateLimitSnapshot, ...]
    dlt_artifacts: DltArtifactResult

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly summary without raw payloads or secrets."""

        return {
            "tenant_id": self.tenant_id,
            "ingestion_run_id": self.ingestion_run_id,
            "fetched_at": self.fetched_at.isoformat(),
            "repository_count": self.repository_count,
            "pull_request_count": self.pull_request_count,
            "writes": [
                {
                    "resource_type": write.resource_type,
                    "table_path": str(write.table_path),
                    "row_count": write.row_count,
                }
                for write in self.writes
            ],
            "rate_limits": [json.loads(rate_limit.to_json()) for rate_limit in self.rate_limits],
            "dlt_artifacts": self.dlt_artifacts.as_dict(),
        }


class GitHubClientProtocol(Protocol):
    """Protocol for live or fixture GitHub extraction clients."""

    def get_paginated(
        self, path: str, *, params: Mapping[str, str | int] | None = None
    ) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]: ...

    def get_paginated_since_updated_at(
        self,
        path: str,
        *,
        updated_since: datetime,
        params: Mapping[str, str | int] | None = None,
    ) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]: ...

    def get_one(self, path: str) -> tuple[dict[str, Any], RateLimitSnapshot]: ...


class GitHubDltSourceContext:
    """Shared dlt source/resource context for one tenant's GitHub bronze extraction."""

    def __init__(
        self,
        *,
        tenant: TenantConfig,
        source_config: GitHubSourceConfig,
        client: GitHubClientProtocol,
        ingestion_run_id: str,
        fetched_at: datetime,
        max_repositories: int | None,
        pull_request_updated_since_by_repo: Mapping[str, datetime] | None = None,
    ) -> None:
        self.tenant = tenant
        self.source_config = source_config
        self.client = client
        self.ingestion_run_id = ingestion_run_id
        self.fetched_at = fetched_at
        self.max_repositories = max_repositories
        self.pull_request_updated_since_by_repo = dict(pull_request_updated_since_by_repo or {})
        self._repositories: list[dict[str, Any]] | None = None
        self._repository_rate_limits: list[RateLimitSnapshot] = []
        self._pull_requests: list[dict[str, Any]] | None = None
        self._pull_request_rate_limits: list[RateLimitSnapshot] = []
        self.resource_states: dict[str, dict[str, Any]] = {}

    def repository_records(self) -> list[dict[str, Any]]:
        """Return dlt resource rows for repositories while recording resource state."""

        repositories, rate_limits = self._fetch_repositories()
        latest_rate_limit = rate_limits[-1] if rate_limits else None
        records = [
            repository_payload_to_bronze_record(
                tenant_id=self.tenant.tenant_id,
                payload=repository,
                fetched_at=self.fetched_at,
                ingestion_run_id=self.ingestion_run_id,
                rate_limit=latest_rate_limit,
            )
            for repository in repositories
        ]
        self._record_resource_state(
            REPOSITORY_RESOURCE, row_count=len(records), rate_limits=rate_limits
        )
        return records

    def pull_request_records(self) -> list[dict[str, Any]]:
        """Return dlt resource rows for pull requests while recording resource state."""

        pull_requests, rate_limits = self._fetch_pull_requests()
        latest_rate_limit = rate_limits[-1] if rate_limits else None
        records = [
            pull_request_payload_to_bronze_record(
                tenant_id=self.tenant.tenant_id,
                payload=pull_request,
                fetched_at=self.fetched_at,
                ingestion_run_id=self.ingestion_run_id,
                rate_limit=latest_rate_limit,
            )
            for pull_request in pull_requests
        ]
        self._record_resource_state(
            PULL_REQUEST_RESOURCE, row_count=len(records), rate_limits=rate_limits
        )
        return records

    def rate_limits(self) -> tuple[RateLimitSnapshot, ...]:
        """Return all observed rate-limit snapshots in resource order."""

        return tuple(self._repository_rate_limits + self._pull_request_rate_limits)

    def source_state_snapshot(self) -> dict[str, Any]:
        """Return a serializable dlt source-state snapshot for local inspection."""

        return {
            "schema_version": DLT_ARTIFACT_SCHEMA_VERSION,
            "source_name": DLT_BRONZE_SOURCE_NAME,
            "tenant_id": self.tenant.tenant_id,
            "source": GITHUB_SOURCE,
            "ingestion_run_id": self.ingestion_run_id,
            "fetched_at": self.fetched_at.isoformat(),
            "resources": self.resource_states,
        }

    def _fetch_repositories(self) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
        if self._repositories is None:
            repositories, rate_limits = fetch_configured_repositories(
                self.client, self.source_config, max_repositories=self.max_repositories
            )
            self._repositories = repositories
            self._repository_rate_limits = rate_limits
        return self._repositories, self._repository_rate_limits

    def _fetch_pull_requests(self) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
        if self._pull_requests is None:
            repositories, _rate_limits = self._fetch_repositories()
            pull_requests, rate_limits = fetch_pull_requests_for_repositories(
                self.client,
                repositories,
                updated_since_by_repo=self.pull_request_updated_since_by_repo,
            )
            self._pull_requests = pull_requests
            self._pull_request_rate_limits = rate_limits
        return self._pull_requests, self._pull_request_rate_limits

    def _record_resource_state(
        self, resource_type: str, *, row_count: int, rate_limits: Sequence[RateLimitSnapshot]
    ) -> None:
        latest_rate_limit = rate_limits[-1] if rate_limits else None
        self.resource_states[resource_type] = {
            "resource_type": resource_type,
            "write_disposition": "replace",
            "row_count": row_count,
            "latest_rate_limit": (
                json.loads(latest_rate_limit.to_json()) if latest_rate_limit else None
            ),
        }


class GitHubRestClient:
    """Small dlt-backed GitHub REST client with pagination and header capture.

    The project keeps this wrapper deliberately thin: dlt's ``RESTClient`` and
    ``HeaderLinkPaginator`` own API extraction/pagination while this class preserves the
    existing bronze ingestion contract and rate-limit metadata shape.
    """

    def __init__(
        self,
        *,
        api_base_url: str,
        token: str,
        user_agent: str = DEFAULT_USER_AGENT,
        session: requests.Session | None = None,
        rest_client: RESTClient | None = None,
    ) -> None:
        self._owned_session = session is None and rest_client is None
        rest_client_kwargs: dict[str, Any] = {
            "base_url": api_base_url.rstrip("/") + "/",
            "headers": {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
                "User-Agent": user_agent,
            },
            "auth": BearerTokenAuth(token),
            "paginator": HeaderLinkPaginator(),
        }
        if session is not None:
            rest_client_kwargs["session"] = session
        self._rest_client = rest_client or RESTClient(**rest_client_kwargs)

    def close(self) -> None:
        """Close the underlying dlt REST session if this wrapper owns it."""

        if self._owned_session:
            self._rest_client.session.close()

    def get_paginated(
        self, path: str, *, params: Mapping[str, str | int] | None = None
    ) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
        """GET all pages for a list-returning endpoint via dlt REST pagination."""

        items: list[dict[str, Any]] = []
        rate_limits: list[RateLimitSnapshot] = []
        for page in self._rest_client.paginate(path, params=dict(params or {})):
            response = page.response
            rate_limits.append(RateLimitSnapshot.from_headers(response.headers))
            _raise_for_status(response)
            page_items = list(page)
            items.extend(_ensure_mapping_items(page_items, endpoint=path))

        return items, rate_limits

    def get_paginated_since_updated_at(
        self,
        path: str,
        *,
        updated_since: datetime,
        params: Mapping[str, str | int] | None = None,
    ) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
        """GET pages sorted by updated_at desc and stop after the incremental cutoff."""

        items: list[dict[str, Any]] = []
        rate_limits: list[RateLimitSnapshot] = []
        for page in self._rest_client.paginate(path, params=dict(params or {})):
            response = page.response
            rate_limits.append(RateLimitSnapshot.from_headers(response.headers))
            _raise_for_status(response)
            page_items = _ensure_mapping_items(list(page), endpoint=path)
            if not page_items:
                continue
            for item in page_items:
                item_updated_at = _github_timestamp(item.get("updated_at"))
                if item_updated_at is None or item_updated_at >= updated_since:
                    items.append(item)
            oldest_page_update = _oldest_github_updated_at(page_items)
            if oldest_page_update is not None and oldest_page_update < updated_since:
                break

        return items, rate_limits

    def get_one(self, path: str) -> tuple[dict[str, Any], RateLimitSnapshot]:
        """GET a single object endpoint via dlt's REST client."""

        response = self._rest_client.get(path)
        rate_limit = RateLimitSnapshot.from_headers(response.headers)
        _raise_for_status(response)
        body = response.json()
        if not isinstance(body, dict):
            raise GitHubIngestionError(f"Expected object response from GitHub endpoint {path}")
        return dict(body), rate_limit

    def dlt_backend_summary(self) -> dict[str, str]:
        """Return the dlt extraction primitives used by this client for validation/docs."""

        return {
            "source": DLT_BRONZE_SOURCE_NAME,
            "client": type(self._rest_client).__name__,
            "paginator": type(self._rest_client.paginator).__name__,
        }

    def __enter__(self) -> GitHubRestClient:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()


def build_github_bronze_dlt_source(context: GitHubDltSourceContext) -> DltSource:
    """Build the explicit dlt source/resources for one tenant GitHub bronze run."""

    @dlt.resource(  # type: ignore[call-overload,untyped-decorator]
        name=REPOSITORY_RESOURCE,
        table_name=REPOSITORY_RESOURCE,
        write_disposition="replace",
        columns=DLT_BRONZE_COLUMNS,
        primary_key="source_id",
    )
    def repositories() -> Iterable[dict[str, Any]]:
        records = context.repository_records()
        _update_dlt_state(context, REPOSITORY_RESOURCE)
        yield from records

    @dlt.resource(  # type: ignore[call-overload,untyped-decorator]
        name=PULL_REQUEST_RESOURCE,
        table_name=PULL_REQUEST_RESOURCE,
        write_disposition="replace",
        columns=DLT_BRONZE_COLUMNS,
        primary_key="source_id",
    )
    def pull_requests() -> Iterable[dict[str, Any]]:
        records = context.pull_request_records()
        _update_dlt_state(context, PULL_REQUEST_RESOURCE)
        yield from records

    @dlt.source(name=DLT_BRONZE_SOURCE_NAME, schema_contract="evolve")
    def github_bronze() -> tuple[Any, Any]:
        return repositories, pull_requests

    return github_bronze()


def _update_dlt_state(context: GitHubDltSourceContext, resource_type: str) -> None:
    """Update dlt source/resource state for visibility during extraction."""

    resource_state = context.resource_states[resource_type]
    dlt.current.resource_state().update(resource_state)
    source_state = dlt.current.source_state()
    source_state.update(
        {
            "source_name": DLT_BRONZE_SOURCE_NAME,
            "tenant_id": context.tenant.tenant_id,
            "source": GITHUB_SOURCE,
            "ingestion_run_id": context.ingestion_run_id,
            "fetched_at": context.fetched_at.isoformat(),
        }
    )
    source_state.setdefault("resources", {})[resource_type] = resource_state


def ingest_tenant_github_to_bronze(
    tenant: TenantConfig,
    *,
    token: str | None = None,
    ingestion_run_id: str | None = None,
    fetched_at: datetime | None = None,
    client: GitHubRestClient | None = None,
    max_repositories: int | None = None,
) -> GitHubBronzeIngestionResult:
    """Ingest one configured tenant's dlt GitHub source to bronze Delta.

    Bronze tables are overwritten per tenant/resource. For this first batch-style source,
    overwrite semantics make repeated runs idempotent for the configured scope while raw
    payloads, run metadata, and dlt schema/state artifacts remain visible.
    """

    run_id = ingestion_run_id or str(uuid.uuid4())
    run_fetched_at = fetched_at or datetime.now(tz=UTC)
    source_config = tenant.github
    incremental_state = load_incremental_state(tenant.tenant_id)
    updated_since_by_repo = _pull_request_updated_since_by_repo(incremental_state)
    if _fixture_mode_enabled():
        repository_records, pull_request_records, context, dlt_source = _fixture_bronze_records(
            tenant,
            source_config=source_config,
            ingestion_run_id=run_id,
            fetched_at=run_fetched_at,
        )
    else:
        github_token = token if token is not None else _token_from_env(source_config)
        owned_client = client is None
        github = client or GitHubRestClient(
            api_base_url=source_config.api_base_url,
            token=github_token,
        )

        context = GitHubDltSourceContext(
            tenant=tenant,
            source_config=source_config,
            client=github,
            ingestion_run_id=run_id,
            fetched_at=run_fetched_at,
            max_repositories=max_repositories,
            pull_request_updated_since_by_repo=updated_since_by_repo,
        )
        dlt_source = build_github_bronze_dlt_source(context)

        try:
            repository_records = list(dlt_source.resources[REPOSITORY_RESOURCE])
            pull_request_records = list(dlt_source.resources[PULL_REQUEST_RESOURCE])
        finally:
            if owned_client:
                github.close()

    repository_path = delta_table_path(
        tenant.tenant_id, "bronze", GITHUB_SOURCE, REPOSITORY_RESOURCE
    )
    pull_request_path = delta_table_path(
        tenant.tenant_id, "bronze", GITHUB_SOURCE, PULL_REQUEST_RESOURCE
    )
    write_bronze_records(repository_path, repository_records)
    if _incremental_enabled() and not _fixture_mode_enabled():
        pull_request_records = merge_bronze_records(pull_request_path, pull_request_records)
        write_incremental_state(tenant.tenant_id, incremental_state, pull_request_records)
    else:
        write_bronze_records(pull_request_path, pull_request_records)
    dlt_artifacts = write_dlt_artifacts(tenant.tenant_id, dlt_source, context)

    return GitHubBronzeIngestionResult(
        tenant_id=tenant.tenant_id,
        ingestion_run_id=run_id,
        fetched_at=run_fetched_at,
        repository_count=len(repository_records),
        pull_request_count=len(pull_request_records),
        writes=(
            BronzeWriteResult(REPOSITORY_RESOURCE, repository_path, len(repository_records)),
            BronzeWriteResult(PULL_REQUEST_RESOURCE, pull_request_path, len(pull_request_records)),
        ),
        rate_limits=context.rate_limits(),
        dlt_artifacts=dlt_artifacts,
    )


def _fixture_mode_enabled() -> bool:
    configured = os.environ.get(GITHUB_FIXTURE_MODE_ENV, "")
    return configured.lower() in {"1", "true", "yes", "on"}


def _fixture_bronze_records(
    tenant: TenantConfig,
    *,
    source_config: GitHubSourceConfig,
    ingestion_run_id: str,
    fetched_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], GitHubDltSourceContext, DltSource]:
    repository_full_name = _fixture_repository_full_name(source_config)
    repository_payload = _fixture_repository_payload(repository_full_name)
    pull_request_payload = _fixture_pull_request_payload(repository_full_name)
    context = GitHubDltSourceContext(
        tenant=tenant,
        source_config=source_config,
        client=_FixtureGitHubClient(repository_payload, pull_request_payload),
        ingestion_run_id=ingestion_run_id,
        fetched_at=fetched_at,
        max_repositories=1,
    )
    dlt_source = build_github_bronze_dlt_source(context)
    repository_records = list(dlt_source.resources[REPOSITORY_RESOURCE])
    pull_request_records = list(dlt_source.resources[PULL_REQUEST_RESOURCE])
    return repository_records, pull_request_records, context, dlt_source


class _FixtureGitHubClient:
    def __init__(self, repository_payload: dict[str, Any], pull_request_payload: dict[str, Any]):
        self._repository_payload = repository_payload
        self._pull_request_payload = pull_request_payload

    def get_paginated(
        self, path: str, *, params: Mapping[str, str | int] | None = None
    ) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
        del params
        if path.endswith("/repos"):
            return [self._repository_payload], [_fixture_rate_limit(remaining=4999)]
        if path.endswith("/pulls"):
            return [self._pull_request_payload], [_fixture_rate_limit(remaining=4998)]
        raise GitHubIngestionError(f"Unexpected fixture GitHub paginated path: {path}")

    def get_paginated_since_updated_at(
        self,
        path: str,
        *,
        updated_since: datetime,
        params: Mapping[str, str | int] | None = None,
    ) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
        records, rate_limits = self.get_paginated(path, params=params)
        return [
            record
            for record in records
            if (_github_timestamp(record.get("updated_at")) or datetime.min.replace(tzinfo=UTC))
            >= updated_since
        ], rate_limits

    def get_one(self, path: str) -> tuple[dict[str, Any], RateLimitSnapshot]:
        if path.startswith("/repos/"):
            return self._repository_payload, _fixture_rate_limit(remaining=4997)
        raise GitHubIngestionError(f"Unexpected fixture GitHub object path: {path}")


def _fixture_repository_full_name(source_config: GitHubSourceConfig) -> str:
    if source_config.repositories:
        return source_config.repositories[0]
    if source_config.owners:
        return f"{source_config.owners[0]}/kabuto-kurage-fixture"
    return "octocat/Hello-World"


def _fixture_repository_payload(full_name: str) -> dict[str, Any]:
    owner, name = full_name.split("/", 1)
    return {
        "id": 1296269,
        "node_id": f"fixture-repository-{owner}-{name}",
        "name": name,
        "full_name": full_name,
        "owner": {"login": owner},
        "html_url": f"https://github.com/{full_name}",
        "url": f"https://api.github.com/repos/{full_name}",
        "private": False,
        "fork": False,
        "archived": False,
        "disabled": False,
        "default_branch": "main",
        "language": "Python",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "pushed_at": "2026-06-02T00:00:00Z",
    }


def _fixture_pull_request_payload(full_name: str) -> dict[str, Any]:
    return {
        "id": 1,
        "node_id": f"fixture-pull-request-{full_name.replace('/', '-')}",
        "number": 1,
        "state": "closed",
        "title": "Fixture PR for Dagster materialization smoke test",
        "user": {"login": "octocat"},
        "author_association": "OWNER",
        "draft": False,
        "html_url": f"https://github.com/{full_name}/pull/1",
        "url": f"https://api.github.com/repos/{full_name}/pulls/1",
        "base": {"ref": "main", "repo": {"full_name": full_name}},
        "head": {"ref": "fixture", "repo": {"full_name": full_name}},
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T12:00:00Z",
        "closed_at": "2026-06-02T00:00:00Z",
        "merged_at": "2026-06-02T00:00:00Z",
    }


def _fixture_rate_limit(*, remaining: int) -> RateLimitSnapshot:
    return RateLimitSnapshot(
        limit=5000,
        remaining=remaining,
        used=5000 - remaining,
        reset_epoch_seconds=1781800000,
        resource="fixture",
    )


def write_dlt_artifacts(
    tenant_id: str, dlt_source: DltSource, context: GitHubDltSourceContext
) -> DltArtifactResult:
    """Write local dlt schema/state artifacts for one bronze ingestion run."""

    artifact_root = _dlt_artifact_root(tenant_id)
    artifact_root.mkdir(parents=True, exist_ok=True)
    schema_path = artifact_root / "schema.json"
    state_path = artifact_root / "state.json"
    schema_path.write_text(
        json.dumps(_dlt_schema_artifact(dlt_source), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    state_path.write_text(
        json.dumps(context.source_state_snapshot(), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return DltArtifactResult(
        source_name=DLT_BRONZE_SOURCE_NAME,
        resource_names=(REPOSITORY_RESOURCE, PULL_REQUEST_RESOURCE),
        schema_path=schema_path,
        state_path=state_path,
    )


def _dlt_schema_artifact(dlt_source: DltSource) -> dict[str, Any]:
    return {
        "schema_version": DLT_ARTIFACT_SCHEMA_VERSION,
        "source_name": dlt_source.name,
        "source_schema": dlt_source.schema.to_dict(),
        "resource_schemas": {
            resource_name: dlt_source.resources[resource_name].compute_table_schema()
            for resource_name in (REPOSITORY_RESOURCE, PULL_REQUEST_RESOURCE)
        },
    }


def _dlt_artifact_root(tenant_id: str) -> Path:
    return data_root() / "dlt" / GITHUB_SOURCE / tenant_id


def fetch_configured_repositories(
    client: GitHubClientProtocol,
    source_config: GitHubSourceConfig,
    *,
    max_repositories: int | None = None,
) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
    """Fetch repositories for configured owners and explicit repository full names."""

    repositories_by_full_name: dict[str, dict[str, Any]] = {}
    rate_limits: list[RateLimitSnapshot] = []

    for owner in source_config.owners:
        owner_repositories, owner_rate_limits = client.get_paginated(
            f"/users/{owner}/repos",
            params={"per_page": 100, "type": "all", "sort": "updated", "direction": "desc"},
        )
        rate_limits.extend(owner_rate_limits)
        for repository in owner_repositories:
            full_name = _string_or_empty(repository.get("full_name"))
            if full_name:
                repositories_by_full_name[full_name] = repository

    for repository_full_name in source_config.repositories:
        repository, rate_limit = client.get_one(f"/repos/{repository_full_name}")
        rate_limits.append(rate_limit)
        full_name = _string_or_empty(repository.get("full_name")) or repository_full_name
        repositories_by_full_name[full_name] = repository

    repositories = sorted(
        repositories_by_full_name.values(), key=lambda item: str(item.get("full_name", ""))
    )
    if max_repositories is not None:
        repositories = repositories[:max_repositories]
    return repositories, rate_limits


def fetch_pull_requests_for_repositories(
    client: GitHubClientProtocol,
    repositories: Sequence[Mapping[str, Any]],
    *,
    updated_since_by_repo: Mapping[str, datetime] | None = None,
) -> tuple[list[dict[str, Any]], list[RateLimitSnapshot]]:
    """Fetch pull requests for each repository, using updated_at cutoffs when available."""

    pull_requests: list[dict[str, Any]] = []
    rate_limits: list[RateLimitSnapshot] = []
    for repository in repositories:
        full_name = repository.get("full_name")
        if not isinstance(full_name, str) or not full_name:
            continue
        params: dict[str, str | int] = {
            "per_page": 100,
            "state": "all",
            "sort": "updated",
            "direction": "desc",
        }
        updated_since = (updated_since_by_repo or {}).get(full_name)
        if updated_since is None:
            repository_pull_requests, repository_rate_limits = client.get_paginated(
                f"/repos/{full_name}/pulls",
                params=params,
            )
        else:
            repository_pull_requests, repository_rate_limits = (
                client.get_paginated_since_updated_at(
                    f"/repos/{full_name}/pulls",
                    updated_since=updated_since,
                    params=params,
                )
            )
        rate_limits.extend(repository_rate_limits)
        pull_requests.extend(repository_pull_requests)
    return pull_requests, rate_limits


def repository_payload_to_bronze_record(
    *,
    tenant_id: str,
    payload: Mapping[str, Any],
    fetched_at: datetime,
    ingestion_run_id: str,
    rate_limit: RateLimitSnapshot | None,
) -> dict[str, Any]:
    """Normalize a raw GitHub repository payload into a bronze record."""

    owner = payload.get("owner") if isinstance(payload.get("owner"), Mapping) else {}
    owner_login = _string_or_none(owner.get("login") if isinstance(owner, Mapping) else None)
    full_name = _string_or_none(payload.get("full_name"))
    return _bronze_record(
        tenant_id=tenant_id,
        resource_type=REPOSITORY_RESOURCE,
        fetched_at=fetched_at,
        source_id=_source_id(payload),
        source_owner=owner_login,
        source_repo=full_name,
        source_url=_string_or_none(payload.get("html_url")),
        api_url=_string_or_none(payload.get("url")),
        ingestion_run_id=ingestion_run_id,
        payload=payload,
        rate_limit=rate_limit,
    )


def pull_request_payload_to_bronze_record(
    *,
    tenant_id: str,
    payload: Mapping[str, Any],
    fetched_at: datetime,
    ingestion_run_id: str,
    rate_limit: RateLimitSnapshot | None,
) -> dict[str, Any]:
    """Normalize a raw GitHub pull request payload into a bronze record."""

    repository_full_name = _pull_request_repository_full_name(payload)
    source_owner = repository_full_name.split("/", 1)[0] if repository_full_name else None
    return _bronze_record(
        tenant_id=tenant_id,
        resource_type=PULL_REQUEST_RESOURCE,
        fetched_at=fetched_at,
        source_id=_source_id(payload),
        source_owner=source_owner,
        source_repo=repository_full_name,
        source_url=_string_or_none(payload.get("html_url")),
        api_url=_string_or_none(payload.get("url")),
        ingestion_run_id=ingestion_run_id,
        payload=payload,
        rate_limit=rate_limit,
    )


def write_bronze_records(table_path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    """Overwrite a bronze Delta table with the latest snapshot for a tenant/resource."""

    table_path.parent.mkdir(parents=True, exist_ok=True)
    write_deltalake(str(table_path), _records_to_arrow_table(records), mode="overwrite")


def merge_bronze_records(
    table_path: Path, changed_records: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Merge changed bronze records with an existing Delta snapshot by source_id."""

    records_by_source_id = {
        _string_or_empty(record.get("source_id")): dict(record)
        for record in _read_existing_bronze_records(table_path)
        if _string_or_empty(record.get("source_id"))
    }
    for record in changed_records:
        source_id = _string_or_empty(record.get("source_id"))
        if source_id:
            records_by_source_id[source_id] = dict(record)
    records = sorted(
        records_by_source_id.values(),
        key=lambda record: (
            _string_or_empty(record.get("source_repo")),
            _string_or_empty(record.get("source_id")),
        ),
    )
    write_bronze_records(table_path, records)
    return records


def load_incremental_state(tenant_id: str) -> dict[str, Any]:
    """Load tenant-scoped GitHub incremental cursor state from local dlt artifacts."""

    state_path = _incremental_state_path(tenant_id)
    if not _incremental_enabled() or not state_path.exists():
        return {"schema_version": 1, "pull_requests": {}}
    raw = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise GitHubIngestionError(f"Incremental state must be a JSON object: {state_path}")
    raw.setdefault("schema_version", 1)
    raw.setdefault("pull_requests", {})
    return raw


def write_incremental_state(
    tenant_id: str,
    previous_state: Mapping[str, Any],
    pull_request_records: Sequence[Mapping[str, Any]],
) -> None:
    """Persist max pull-request updated_at cursors by repository."""

    state = dict(previous_state)
    pull_requests = dict(state.get("pull_requests") or {})
    for record in pull_request_records:
        payload = _json_mapping(record.get("payload_json"))
        repository = _string_or_none(
            record.get("source_repo")
        ) or _pull_request_repository_full_name(payload)
        updated_at = _github_timestamp(payload.get("updated_at"))
        if repository is None or updated_at is None:
            continue
        current = _github_timestamp(pull_requests.get(repository))
        if current is None or updated_at > current:
            pull_requests[repository] = updated_at.isoformat().replace("+00:00", "Z")
    state.update(
        {
            "schema_version": 1,
            "source": GITHUB_SOURCE,
            "resource_type": PULL_REQUEST_RESOURCE,
            "tenant_id": tenant_id,
            "updated_at": datetime.now(tz=UTC).isoformat(),
            "pull_requests": pull_requests,
        }
    )
    state_path = _incremental_state_path(tenant_id)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _read_existing_bronze_records(table_path: Path) -> list[dict[str, Any]]:
    if not table_path.exists():
        return []
    return [dict(row) for row in DeltaTable(str(table_path)).to_pyarrow_table().to_pylist()]


def _records_to_arrow_table(records: Sequence[Mapping[str, Any]]) -> pa.Table:
    columns: dict[str, list[Any]] = {field.name: [] for field in BRONZE_SCHEMA}
    for record in records:
        for field in BRONZE_SCHEMA:
            columns[field.name].append(record.get(field.name))
    return pa.table(columns, schema=BRONZE_SCHEMA)


def _bronze_record(
    *,
    tenant_id: str,
    resource_type: str,
    fetched_at: datetime,
    source_id: str,
    source_owner: str | None,
    source_repo: str | None,
    source_url: str | None,
    api_url: str | None,
    ingestion_run_id: str,
    payload: Mapping[str, Any],
    rate_limit: RateLimitSnapshot | None,
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "source": GITHUB_SOURCE,
        "resource_type": resource_type,
        "fetched_at": fetched_at,
        "source_id": source_id,
        "source_owner": source_owner,
        "source_repo": source_repo,
        "source_url": source_url,
        "api_url": api_url,
        "ingestion_run_id": ingestion_run_id,
        "payload_json": json.dumps(payload, sort_keys=True, separators=(",", ":")),
        "rate_limit_json": (
            rate_limit or RateLimitSnapshot(None, None, None, None, None)
        ).to_json(),
    }


def _incremental_enabled() -> bool:
    configured = os.environ.get(GITHUB_INCREMENTAL_ENABLED_ENV, "true")
    return configured.lower() not in {"0", "false", "no", "off"}


def _incremental_lookback() -> timedelta:
    configured = os.environ.get(GITHUB_INCREMENTAL_LOOKBACK_DAYS_ENV, "1")
    try:
        days = float(configured)
    except ValueError as exc:
        raise GitHubIngestionError(
            f"{GITHUB_INCREMENTAL_LOOKBACK_DAYS_ENV} must be numeric when set"
        ) from exc
    if days < 0:
        raise GitHubIngestionError(f"{GITHUB_INCREMENTAL_LOOKBACK_DAYS_ENV} cannot be negative")
    return timedelta(days=days)


def _pull_request_updated_since_by_repo(state: Mapping[str, Any]) -> dict[str, datetime]:
    if not _incremental_enabled():
        return {}
    pull_requests = state.get("pull_requests")
    if not isinstance(pull_requests, Mapping):
        return {}
    lookback = _incremental_lookback()
    cutoffs: dict[str, datetime] = {}
    for repository, value in pull_requests.items():
        if not isinstance(repository, str):
            continue
        cursor = _github_timestamp(value)
        if cursor is not None:
            cutoffs[repository] = cursor - lookback
    return cutoffs


def _incremental_state_path(tenant_id: str) -> Path:
    return _dlt_artifact_root(tenant_id) / "incremental_state.json"


def _token_from_env(source_config: GitHubSourceConfig) -> str:
    auth_mode = os.environ.get(GITHUB_AUTH_MODE_ENV, "auto").lower()
    if auth_mode not in {"auto", "pat", "app"}:
        raise GitHubIngestionError(f"{GITHUB_AUTH_MODE_ENV} must be one of auto, pat, or app")
    if auth_mode in {"auto", "pat"}:
        token = os.environ.get(source_config.token_env)
        if not token and source_config.token_env != "GH_TOKEN":
            token = os.environ.get("GH_TOKEN")
        if token:
            return token
        if auth_mode == "pat":
            raise GitHubIngestionError(
                f"GitHub token not found. Set {source_config.token_env}"
                + (" or GH_TOKEN" if source_config.token_env != "GH_TOKEN" else "")
                + "."
            )
    if auth_mode in {"auto", "app"} and _github_app_configured():
        return mint_github_app_installation_token()
    raise GitHubIngestionError(
        f"GitHub token not found. Set {source_config.token_env}"
        + (" or GH_TOKEN" if source_config.token_env != "GH_TOKEN" else "")
        + f", or configure {GITHUB_APP_ID_ENV}, {GITHUB_APP_INSTALLATION_ID_ENV}, and "
        + f"{GITHUB_APP_PRIVATE_KEY_ENV}/{GITHUB_APP_PRIVATE_KEY_PATH_ENV}."
    )


def _github_app_configured() -> bool:
    return bool(
        os.environ.get(GITHUB_APP_ID_ENV)
        and os.environ.get(GITHUB_APP_INSTALLATION_ID_ENV)
        and (
            os.environ.get(GITHUB_APP_PRIVATE_KEY_ENV)
            or os.environ.get(GITHUB_APP_PRIVATE_KEY_PATH_ENV)
        )
    )


def mint_github_app_installation_token(session: requests.Session | None = None) -> str:
    """Mint a short-lived GitHub App installation token from environment configuration."""

    app_id = _required_env(GITHUB_APP_ID_ENV)
    installation_id = _required_env(GITHUB_APP_INSTALLATION_ID_ENV)
    private_key = _github_app_private_key()
    now = int(time.time())
    encoded_jwt = jwt.encode(
        {"iat": now - 60, "exp": now + 9 * 60, "iss": app_id},
        private_key,
        algorithm="RS256",
    )
    http = session or requests.Session()
    response = http.post(
        f"https://api.github.com/app/installations/{installation_id}/access_tokens",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {encoded_jwt}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": DEFAULT_USER_AGENT,
        },
        timeout=30,
    )
    _raise_for_status(response)
    body = response.json()
    token = body.get("token") if isinstance(body, Mapping) else None
    if not isinstance(token, str) or not token:
        raise GitHubIngestionError("GitHub App installation token response did not include token")
    return token


def _github_app_private_key() -> str:
    private_key = os.environ.get(GITHUB_APP_PRIVATE_KEY_ENV)
    if private_key:
        return private_key.replace("\\n", "\n")
    private_key_path = os.environ.get(GITHUB_APP_PRIVATE_KEY_PATH_ENV)
    if not private_key_path:
        raise GitHubIngestionError(
            f"Set {GITHUB_APP_PRIVATE_KEY_ENV} or {GITHUB_APP_PRIVATE_KEY_PATH_ENV}"
        )
    return Path(private_key_path).expanduser().read_text(encoding="utf-8")


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise GitHubIngestionError(f"Missing required GitHub App environment variable: {name}")
    return value


def _raise_for_status(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        rate_limit = RateLimitSnapshot.from_headers(response.headers)
        message = f"GitHub API request failed with HTTP {response.status_code} for {response.url}"
        if response.status_code in {403, 429} and rate_limit.remaining == 0:
            message += "; rate limit appears exhausted"
        raise GitHubIngestionError(message) from exc


def _ensure_mapping_items(items: Iterable[Any], *, endpoint: str) -> list[dict[str, Any]]:
    mapped_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise GitHubIngestionError(f"Expected object items from GitHub endpoint {endpoint}")
        mapped_items.append(dict(item))
    return mapped_items


def _oldest_github_updated_at(items: Sequence[Mapping[str, Any]]) -> datetime | None:
    values = [_github_timestamp(item.get("updated_at")) for item in items]
    present = [value for value in values if value is not None]
    return min(present) if present else None


def _github_timestamp(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str) or not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _json_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, str) or not value:
        return {}
    parsed = json.loads(value)
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _source_id(payload: Mapping[str, Any]) -> str:
    for key in ("node_id", "id", "url"):
        value = payload.get(key)
        if value is not None:
            return str(value)
    raise GitHubIngestionError("GitHub payload is missing node_id, id, and url")


def _pull_request_repository_full_name(payload: Mapping[str, Any]) -> str | None:
    base = payload.get("base")
    if isinstance(base, Mapping):
        repo = base.get("repo")
        if isinstance(repo, Mapping):
            full_name = _string_or_none(repo.get("full_name"))
            if full_name:
                return full_name
    head = payload.get("head")
    if isinstance(head, Mapping):
        repo = head.get("repo")
        if isinstance(repo, Mapping):
            return _string_or_none(repo.get("full_name"))
    return None


def _optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _string_or_empty(value: object) -> str:
    return value if isinstance(value, str) else ""


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the bronze ingestion utility."""

    parser = argparse.ArgumentParser(description="Ingest configured GitHub data to bronze Delta.")
    parser.add_argument("--tenant", action="append", dest="tenants", help="Tenant ID to ingest.")
    parser.add_argument(
        "--all-tenants", action="store_true", help="Ingest all tenants from the registry."
    )
    parser.add_argument(
        "--data-root",
        help="Override KABUTO_DATA_ROOT for this run. Useful for live validation in temp dirs.",
    )
    parser.add_argument(
        "--max-repositories",
        type=int,
        help="Limit repositories processed after discovery; intended for safe validation runs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for manually running bronze ingestion."""

    args = parse_args(argv)
    if args.data_root:
        os.environ["KABUTO_DATA_ROOT"] = args.data_root

    registry = load_tenant_registry()
    tenant_ids = tuple(args.tenants or ())
    if args.all_tenants:
        tenant_ids = registry.tenant_ids
    if not tenant_ids:
        raise SystemExit("Pass --tenant TENANT_ID or --all-tenants")

    results = [
        ingest_tenant_github_to_bronze(
            registry.get(tenant_id), max_repositories=args.max_repositories
        )
        for tenant_id in tenant_ids
    ]
    print(
        json.dumps(
            {
                "data_root": str(data_root()),
                "results": [result.as_dict() for result in results],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
