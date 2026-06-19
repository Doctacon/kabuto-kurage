"""Gold GitHub engineering metrics derived from tenant-scoped silver models."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from kabuto_kurage.ingestion.github_bronze import GITHUB_SOURCE, PULL_REQUEST_RESOURCE
from kabuto_kurage.paths import data_root, delta_table_path
from kabuto_kurage.tenancy import load_tenant_registry, validate_tenant_id

PR_THROUGHPUT_DAILY_TABLE = "pr_throughput_daily"
PR_CYCLE_TIME_TABLE = "pr_cycle_time"

PR_THROUGHPUT_DAILY_SCHEMA = pa.schema(
    [
        ("tenant_id", pa.string()),
        ("source", pa.string()),
        ("repository_full_name", pa.string()),
        ("metric_date", pa.date32()),
        ("opened_count", pa.int64()),
        ("merged_count", pa.int64()),
        ("closed_count", pa.int64()),
        ("observed_pull_request_count", pa.int64()),
        ("latest_fetched_at", pa.timestamp("us", tz="UTC")),
        ("latest_ingestion_run_id", pa.string()),
    ]
)

PR_CYCLE_TIME_SCHEMA = pa.schema(
    [
        ("tenant_id", pa.string()),
        ("source", pa.string()),
        ("repository_full_name", pa.string()),
        ("repository_owner", pa.string()),
        ("pull_request_id", pa.int64()),
        ("pull_request_node_id", pa.string()),
        ("number", pa.int64()),
        ("title", pa.string()),
        ("user_login", pa.string()),
        ("state", pa.string()),
        ("merged", pa.bool_()),
        ("created_at", pa.timestamp("us", tz="UTC")),
        ("merged_at", pa.timestamp("us", tz="UTC")),
        ("cycle_time_hours", pa.float64()),
        ("cycle_time_days", pa.float64()),
        ("fetched_at", pa.timestamp("us", tz="UTC")),
        ("ingestion_run_id", pa.string()),
    ]
)


class GitHubGoldMetricError(RuntimeError):
    """Raised when GitHub silver-to-gold metric computation cannot proceed."""


@dataclass(frozen=True)
class GoldWriteResult:
    """Summary for one gold Delta write."""

    table_name: str
    table_path: Path
    row_count: int


@dataclass(frozen=True)
class GitHubGoldMetricResult:
    """Summary for one tenant's GitHub gold metric materialization."""

    tenant_id: str
    writes: tuple[GoldWriteResult, ...]

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


def materialize_tenant_github_gold(tenant_id: str) -> GitHubGoldMetricResult:
    """Materialize GitHub gold metric Delta tables for one tenant."""

    safe_tenant_id = validate_tenant_id(tenant_id)
    pull_request_rows = _read_silver_pull_request_rows(safe_tenant_id)

    throughput_rows = compute_pr_throughput_daily(pull_request_rows)
    cycle_time_rows = compute_pr_cycle_time(pull_request_rows)

    throughput_path = delta_table_path(
        safe_tenant_id, "gold", GITHUB_SOURCE, PR_THROUGHPUT_DAILY_TABLE
    )
    cycle_time_path = delta_table_path(safe_tenant_id, "gold", GITHUB_SOURCE, PR_CYCLE_TIME_TABLE)

    _write_gold_records(throughput_path, throughput_rows, PR_THROUGHPUT_DAILY_SCHEMA)
    _write_gold_records(cycle_time_path, cycle_time_rows, PR_CYCLE_TIME_SCHEMA)

    return GitHubGoldMetricResult(
        tenant_id=safe_tenant_id,
        writes=(
            GoldWriteResult(PR_THROUGHPUT_DAILY_TABLE, throughput_path, len(throughput_rows)),
            GoldWriteResult(PR_CYCLE_TIME_TABLE, cycle_time_path, len(cycle_time_rows)),
        ),
    )


def compute_pr_throughput_daily(
    pull_request_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Compute daily PR opened/merged/closed counts by tenant and repository.

    A PR can contribute to multiple dates: opened on its `created_at` date, merged on
    its `merged_at` date, and closed on its `closed_at` date. This intentionally keeps
    the first toy throughput metric simple and auditable.
    """

    groups: dict[tuple[str | None, str | None, str | None, date], dict[str, Any]] = {}
    for row in pull_request_rows:
        tenant_id = _string_or_none(row.get("tenant_id"))
        source = _string_or_none(row.get("source")) or GITHUB_SOURCE
        repository_full_name = _string_or_none(row.get("repository_full_name"))
        latest_fetched_at = _timestamp_or_none(row.get("fetched_at"))
        latest_ingestion_run_id = _string_or_none(row.get("ingestion_run_id"))

        for event_name, timestamp in [
            ("opened_count", _timestamp_or_none(row.get("created_at"))),
            ("merged_count", _timestamp_or_none(row.get("merged_at"))),
            ("closed_count", _timestamp_or_none(row.get("closed_at"))),
        ]:
            if timestamp is None:
                continue
            key = (tenant_id, source, repository_full_name, timestamp.date())
            group = groups.setdefault(
                key,
                {
                    "tenant_id": tenant_id,
                    "source": source,
                    "repository_full_name": repository_full_name,
                    "metric_date": timestamp.date(),
                    "opened_count": 0,
                    "merged_count": 0,
                    "closed_count": 0,
                    "observed_pull_request_count": 0,
                    "latest_fetched_at": latest_fetched_at,
                    "latest_ingestion_run_id": latest_ingestion_run_id,
                    "_seen_pull_request_ids": set(),
                },
            )
            group[event_name] += 1
            pull_request_id = _pull_request_identity(row)
            group["_seen_pull_request_ids"].add(pull_request_id)
            if _timestamp_sort_value(latest_fetched_at) >= _timestamp_sort_value(
                group["latest_fetched_at"]
            ):
                group["latest_fetched_at"] = latest_fetched_at
                group["latest_ingestion_run_id"] = latest_ingestion_run_id

    results: list[dict[str, Any]] = []
    for group in groups.values():
        seen_ids = group.pop("_seen_pull_request_ids")
        group["observed_pull_request_count"] = len(seen_ids)
        results.append(group)

    return sorted(
        results,
        key=lambda row: (
            row["tenant_id"] or "",
            row["repository_full_name"] or "",
            row["metric_date"],
        ),
    )


def compute_pr_cycle_time(
    pull_request_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Compute per-PR open-to-merge duration rows from silver pull requests."""

    records: list[dict[str, Any]] = []
    for row in pull_request_rows:
        created_at = _timestamp_or_none(row.get("created_at"))
        merged_at = _timestamp_or_none(row.get("merged_at"))
        cycle_time_hours = _cycle_time_hours(created_at, merged_at)
        records.append(
            {
                "tenant_id": _string_or_none(row.get("tenant_id")),
                "source": _string_or_none(row.get("source")) or GITHUB_SOURCE,
                "repository_full_name": _string_or_none(row.get("repository_full_name")),
                "repository_owner": _string_or_none(row.get("repository_owner")),
                "pull_request_id": _int_or_none(row.get("pull_request_id")),
                "pull_request_node_id": _string_or_none(row.get("pull_request_node_id")),
                "number": _int_or_none(row.get("number")),
                "title": _string_or_none(row.get("title")),
                "user_login": _string_or_none(row.get("user_login")),
                "state": _string_or_none(row.get("state")),
                "merged": _bool_or_none(row.get("merged")),
                "created_at": created_at,
                "merged_at": merged_at,
                "cycle_time_hours": cycle_time_hours,
                "cycle_time_days": (
                    round(cycle_time_hours / 24.0, 6) if cycle_time_hours is not None else None
                ),
                "fetched_at": _timestamp_or_none(row.get("fetched_at")),
                "ingestion_run_id": _string_or_none(row.get("ingestion_run_id")),
            }
        )

    return sorted(
        records,
        key=lambda row: (
            row["tenant_id"] or "",
            row["repository_full_name"] or "",
            row["number"] if row["number"] is not None else -1,
        ),
    )


def _read_silver_pull_request_rows(tenant_id: str) -> list[dict[str, Any]]:
    table_path = delta_table_path(tenant_id, "silver", GITHUB_SOURCE, PULL_REQUEST_RESOURCE)
    if not table_path.exists():
        raise GitHubGoldMetricError(
            f"Silver GitHub pull_requests table does not exist for tenant {tenant_id}: {table_path}"
        )
    rows = DeltaTable(str(table_path)).to_pyarrow_table().to_pylist()
    return cast(list[dict[str, Any]], rows)


def _write_gold_records(
    table_path: Path, records: Sequence[Mapping[str, Any]], schema: pa.Schema
) -> None:
    table_path.parent.mkdir(parents=True, exist_ok=True)
    columns: dict[str, list[Any]] = {field.name: [] for field in schema}
    for record in records:
        for field in schema:
            columns[field.name].append(record.get(field.name))
    write_deltalake(str(table_path), pa.table(columns, schema=schema), mode="overwrite")


def _cycle_time_hours(created_at: datetime | None, merged_at: datetime | None) -> float | None:
    if created_at is None or merged_at is None or merged_at < created_at:
        return None
    return round((merged_at - created_at).total_seconds() / 3600.0, 6)


def _pull_request_identity(row: Mapping[str, Any]) -> str:
    for key in ("pull_request_node_id", "pull_request_id", "api_url"):
        value = row.get(key)
        if value is not None:
            return str(value)
    return json.dumps(
        {
            "repository_full_name": row.get("repository_full_name"),
            "number": row.get("number"),
            "created_at": str(row.get("created_at")),
        },
        sort_keys=True,
    )


def _timestamp_sort_value(value: datetime | None) -> float:
    if value is None:
        return float("-inf")
    return value.timestamp()


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
        return value
    return None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the gold metric utility."""

    parser = argparse.ArgumentParser(description="Build gold GitHub metrics from silver models.")
    parser.add_argument("--tenant", action="append", dest="tenants", help="Tenant ID to transform.")
    parser.add_argument(
        "--all-tenants", action="store_true", help="Build gold metrics for all tenants."
    )
    parser.add_argument(
        "--data-root",
        help="Override KABUTO_DATA_ROOT for this run. Useful for validation in temp dirs.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for manually building gold metrics."""

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
        materialize_tenant_github_gold(registry.get(tenant_id).tenant_id)
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
