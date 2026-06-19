"""Silver GitHub models derived from tenant-scoped bronze Delta tables.

Bronze tables preserve raw GitHub API payloads. This module extracts stable,
typed repository and pull-request columns for downstream analytics while keeping
tenant identity and source traceability explicit.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from kabuto_kurage.ingestion.github_bronze import (
    GITHUB_SOURCE,
    PULL_REQUEST_RESOURCE,
    REPOSITORY_RESOURCE,
)
from kabuto_kurage.paths import data_root, delta_table_path
from kabuto_kurage.tenancy import load_tenant_registry, validate_tenant_id

REPOSITORIES_SILVER_SCHEMA = pa.schema(
    [
        ("tenant_id", pa.string()),
        ("source", pa.string()),
        ("repository_id", pa.int64()),
        ("repository_node_id", pa.string()),
        ("owner_login", pa.string()),
        ("name", pa.string()),
        ("full_name", pa.string()),
        ("private", pa.bool_()),
        ("fork", pa.bool_()),
        ("archived", pa.bool_()),
        ("disabled", pa.bool_()),
        ("default_branch", pa.string()),
        ("language", pa.string()),
        ("description", pa.string()),
        ("html_url", pa.string()),
        ("api_url", pa.string()),
        ("created_at", pa.timestamp("us", tz="UTC")),
        ("updated_at", pa.timestamp("us", tz="UTC")),
        ("pushed_at", pa.timestamp("us", tz="UTC")),
        ("fetched_at", pa.timestamp("us", tz="UTC")),
        ("ingestion_run_id", pa.string()),
        ("bronze_source_id", pa.string()),
        ("bronze_source_url", pa.string()),
        ("bronze_api_url", pa.string()),
    ]
)

PULL_REQUESTS_SILVER_SCHEMA = pa.schema(
    [
        ("tenant_id", pa.string()),
        ("source", pa.string()),
        ("pull_request_id", pa.int64()),
        ("pull_request_node_id", pa.string()),
        ("repository_full_name", pa.string()),
        ("repository_owner", pa.string()),
        ("number", pa.int64()),
        ("state", pa.string()),
        ("title", pa.string()),
        ("user_login", pa.string()),
        ("author_association", pa.string()),
        ("draft", pa.bool_()),
        ("merged", pa.bool_()),
        ("created_at", pa.timestamp("us", tz="UTC")),
        ("updated_at", pa.timestamp("us", tz="UTC")),
        ("closed_at", pa.timestamp("us", tz="UTC")),
        ("merged_at", pa.timestamp("us", tz="UTC")),
        ("html_url", pa.string()),
        ("api_url", pa.string()),
        ("base_ref", pa.string()),
        ("head_ref", pa.string()),
        ("base_repo_full_name", pa.string()),
        ("head_repo_full_name", pa.string()),
        ("fetched_at", pa.timestamp("us", tz="UTC")),
        ("ingestion_run_id", pa.string()),
        ("bronze_source_id", pa.string()),
        ("bronze_source_url", pa.string()),
        ("bronze_api_url", pa.string()),
    ]
)


class GitHubSilverTransformError(RuntimeError):
    """Raised when GitHub bronze-to-silver transformation cannot proceed."""


@dataclass(frozen=True)
class SilverWriteResult:
    """Summary for one silver Delta write."""

    table_name: str
    table_path: Path
    row_count: int


@dataclass(frozen=True)
class GitHubSilverTransformResult:
    """Summary for one tenant's GitHub silver transformation."""

    tenant_id: str
    writes: tuple[SilverWriteResult, ...]

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly summary."""

        return {
            "tenant_id": self.tenant_id,
            "writes": [
                {
                    "table_name": write.table_name,
                    "table_path": str(write.table_path),
                    "row_count": write.row_count,
                }
                for write in self.writes
            ],
        }


def materialize_tenant_github_silver(tenant_id: str) -> GitHubSilverTransformResult:
    """Materialize silver GitHub repository and pull-request Delta tables for one tenant."""

    safe_tenant_id = validate_tenant_id(tenant_id)

    repository_bronze_rows = _read_bronze_rows(safe_tenant_id, REPOSITORY_RESOURCE)
    pull_request_bronze_rows = _read_bronze_rows(safe_tenant_id, PULL_REQUEST_RESOURCE)
    _validate_rows_belong_to_tenant(
        repository_bronze_rows,
        safe_tenant_id,
        layer="bronze",
        table_name=REPOSITORY_RESOURCE,
    )
    _validate_rows_belong_to_tenant(
        pull_request_bronze_rows,
        safe_tenant_id,
        layer="bronze",
        table_name=PULL_REQUEST_RESOURCE,
    )

    repository_records = transform_repository_bronze_rows(repository_bronze_rows)
    pull_request_records = transform_pull_request_bronze_rows(pull_request_bronze_rows)
    _validate_rows_belong_to_tenant(
        repository_records,
        safe_tenant_id,
        layer="silver",
        table_name=REPOSITORY_RESOURCE,
    )
    _validate_rows_belong_to_tenant(
        pull_request_records,
        safe_tenant_id,
        layer="silver",
        table_name=PULL_REQUEST_RESOURCE,
    )

    repositories_path = delta_table_path(
        safe_tenant_id, "silver", GITHUB_SOURCE, REPOSITORY_RESOURCE
    )
    pull_requests_path = delta_table_path(
        safe_tenant_id, "silver", GITHUB_SOURCE, PULL_REQUEST_RESOURCE
    )

    _write_silver_records(repositories_path, repository_records, REPOSITORIES_SILVER_SCHEMA)
    _write_silver_records(pull_requests_path, pull_request_records, PULL_REQUESTS_SILVER_SCHEMA)

    return GitHubSilverTransformResult(
        tenant_id=safe_tenant_id,
        writes=(
            SilverWriteResult(REPOSITORY_RESOURCE, repositories_path, len(repository_records)),
            SilverWriteResult(PULL_REQUEST_RESOURCE, pull_requests_path, len(pull_request_records)),
        ),
    )


def transform_repository_bronze_rows(
    bronze_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Transform bronze repository rows into stable silver records."""

    return [_repository_silver_record(row, _payload(row)) for row in bronze_rows]


def transform_pull_request_bronze_rows(
    bronze_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Transform bronze pull-request rows into stable silver records."""

    return [_pull_request_silver_record(row, _payload(row)) for row in bronze_rows]


def _repository_silver_record(
    bronze_row: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, Any]:
    owner = _mapping_or_empty(payload.get("owner"))
    return {
        "tenant_id": _string_or_none(bronze_row.get("tenant_id")),
        "source": _string_or_none(bronze_row.get("source")) or GITHUB_SOURCE,
        "repository_id": _int_or_none(payload.get("id")),
        "repository_node_id": _string_or_none(payload.get("node_id")),
        "owner_login": _string_or_none(owner.get("login"))
        or _string_or_none(bronze_row.get("source_owner")),
        "name": _string_or_none(payload.get("name")),
        "full_name": _string_or_none(payload.get("full_name"))
        or _string_or_none(bronze_row.get("source_repo")),
        "private": _bool_or_none(payload.get("private")),
        "fork": _bool_or_none(payload.get("fork")),
        "archived": _bool_or_none(payload.get("archived")),
        "disabled": _bool_or_none(payload.get("disabled")),
        "default_branch": _string_or_none(payload.get("default_branch")),
        "language": _string_or_none(payload.get("language")),
        "description": _string_or_none(payload.get("description")),
        "html_url": _string_or_none(payload.get("html_url"))
        or _string_or_none(bronze_row.get("source_url")),
        "api_url": _string_or_none(payload.get("url"))
        or _string_or_none(bronze_row.get("api_url")),
        "created_at": _timestamp_or_none(payload.get("created_at")),
        "updated_at": _timestamp_or_none(payload.get("updated_at")),
        "pushed_at": _timestamp_or_none(payload.get("pushed_at")),
        "fetched_at": _timestamp_or_none(bronze_row.get("fetched_at")),
        "ingestion_run_id": _string_or_none(bronze_row.get("ingestion_run_id")),
        "bronze_source_id": _string_or_none(bronze_row.get("source_id")),
        "bronze_source_url": _string_or_none(bronze_row.get("source_url")),
        "bronze_api_url": _string_or_none(bronze_row.get("api_url")),
    }


def _pull_request_silver_record(
    bronze_row: Mapping[str, Any], payload: Mapping[str, Any]
) -> dict[str, Any]:
    user = _mapping_or_empty(payload.get("user"))
    base = _mapping_or_empty(payload.get("base"))
    head = _mapping_or_empty(payload.get("head"))
    base_repo = _mapping_or_empty(base.get("repo"))
    head_repo = _mapping_or_empty(head.get("repo"))
    repository_full_name = _string_or_none(base_repo.get("full_name")) or _string_or_none(
        bronze_row.get("source_repo")
    )
    repository_owner = repository_full_name.split("/", 1)[0] if repository_full_name else None
    merged_at = _timestamp_or_none(payload.get("merged_at"))

    return {
        "tenant_id": _string_or_none(bronze_row.get("tenant_id")),
        "source": _string_or_none(bronze_row.get("source")) or GITHUB_SOURCE,
        "pull_request_id": _int_or_none(payload.get("id")),
        "pull_request_node_id": _string_or_none(payload.get("node_id")),
        "repository_full_name": repository_full_name,
        "repository_owner": repository_owner,
        "number": _int_or_none(payload.get("number")),
        "state": _string_or_none(payload.get("state")),
        "title": _string_or_none(payload.get("title")),
        "user_login": _string_or_none(user.get("login")),
        "author_association": _string_or_none(payload.get("author_association")),
        "draft": _bool_or_none(payload.get("draft")),
        "merged": merged_at is not None,
        "created_at": _timestamp_or_none(payload.get("created_at")),
        "updated_at": _timestamp_or_none(payload.get("updated_at")),
        "closed_at": _timestamp_or_none(payload.get("closed_at")),
        "merged_at": merged_at,
        "html_url": _string_or_none(payload.get("html_url"))
        or _string_or_none(bronze_row.get("source_url")),
        "api_url": _string_or_none(payload.get("url"))
        or _string_or_none(bronze_row.get("api_url")),
        "base_ref": _string_or_none(base.get("ref")),
        "head_ref": _string_or_none(head.get("ref")),
        "base_repo_full_name": _string_or_none(base_repo.get("full_name")),
        "head_repo_full_name": _string_or_none(head_repo.get("full_name")),
        "fetched_at": _timestamp_or_none(bronze_row.get("fetched_at")),
        "ingestion_run_id": _string_or_none(bronze_row.get("ingestion_run_id")),
        "bronze_source_id": _string_or_none(bronze_row.get("source_id")),
        "bronze_source_url": _string_or_none(bronze_row.get("source_url")),
        "bronze_api_url": _string_or_none(bronze_row.get("api_url")),
    }


def _read_bronze_rows(tenant_id: str, resource_type: str) -> list[dict[str, Any]]:
    table_path = delta_table_path(tenant_id, "bronze", GITHUB_SOURCE, resource_type)
    if not table_path.exists():
        raise GitHubSilverTransformError(
            f"Bronze GitHub {resource_type} table does not exist for tenant "
            f"{tenant_id}: {table_path}"
        )
    rows = DeltaTable(str(table_path)).to_pyarrow_table().to_pylist()
    return cast(list[dict[str, Any]], rows)


def _validate_rows_belong_to_tenant(
    rows: Sequence[Mapping[str, Any]],
    tenant_id: str,
    *,
    layer: str,
    table_name: str,
) -> None:
    mismatched_tenant_ids = sorted(
        {str(row.get("tenant_id")) for row in rows if row.get("tenant_id") != tenant_id}
    )
    if mismatched_tenant_ids:
        raise GitHubSilverTransformError(
            f"Refusing to materialize tenant {tenant_id} {layer}/{table_name}: "
            f"found rows for tenant_id values {mismatched_tenant_ids}"
        )


def _write_silver_records(
    table_path: Path, records: Sequence[Mapping[str, Any]], schema: pa.Schema
) -> None:
    table_path.parent.mkdir(parents=True, exist_ok=True)
    columns: dict[str, list[Any]] = {field.name: [] for field in schema}
    for record in records:
        for field in schema:
            columns[field.name].append(record.get(field.name))
    write_deltalake(str(table_path), pa.table(columns, schema=schema), mode="overwrite")


def _payload(bronze_row: Mapping[str, Any]) -> Mapping[str, Any]:
    payload_json = bronze_row.get("payload_json")
    if not isinstance(payload_json, str) or not payload_json:
        return {}
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as exc:
        raise GitHubSilverTransformError("Bronze row contains invalid payload_json") from exc
    if not isinstance(payload, dict):
        return {}
    return payload


def _mapping_or_empty(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _bool_or_none(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _timestamp_or_none(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str) or not value:
        return None
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the silver transformation utility."""

    parser = argparse.ArgumentParser(description="Build silver GitHub Delta models from bronze.")
    parser.add_argument("--tenant", action="append", dest="tenants", help="Tenant ID to transform.")
    parser.add_argument(
        "--all-tenants", action="store_true", help="Transform all tenants from the registry."
    )
    parser.add_argument(
        "--data-root",
        help="Override KABUTO_DATA_ROOT for this run. Useful for validation in temp dirs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for manually running silver transformations."""

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
        materialize_tenant_github_silver(registry.get(tenant_id).tenant_id)
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
