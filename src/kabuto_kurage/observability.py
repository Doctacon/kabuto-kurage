"""Lightweight local observability for tenant-scoped GitHub Delta tables.

This module intentionally stays local and dependency-light. It inspects the Delta tables
that the portfolio project already writes and summarizes operational signals that are
useful in Dagster metadata, CLI output, and docs:

- table existence and row counts by tenant/source/layer/resource;
- latest successful ingestion timestamp/run ID when lineage columns are present;
- freshness lag and fresh/stale/missing/empty/unknown status;
- GitHub rate-limit status captured in bronze `rate_limit_json` rows.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from deltalake import DeltaTable

from kabuto_kurage.ingestion.github_bronze import (
    GITHUB_SOURCE,
    PULL_REQUEST_RESOURCE,
    REPOSITORY_RESOURCE,
)
from kabuto_kurage.paths import data_root, delta_table_path
from kabuto_kurage.tenancy import load_tenant_registry, validate_tenant_id
from kabuto_kurage.transforms.github_gold import PR_CYCLE_TIME_TABLE, PR_THROUGHPUT_DAILY_TABLE

DEFAULT_STALE_AFTER_HOURS = 24.0


@dataclass(frozen=True)
class GitHubTableObservabilityConfig:
    """Observation settings for one known GitHub Delta table."""

    layer: str
    resource_type: str
    freshness_column: str | None
    ingestion_run_column: str | None
    rate_limit_column: str | None = None


@dataclass(frozen=True)
class TableObservability:
    """Operational summary for one tenant/source/layer/resource Delta table."""

    tenant_id: str
    source: str
    layer: str
    resource_type: str
    table_path: Path
    table_exists: bool
    row_count: int
    delta_version: int | None
    latest_successful_ingestion_at: datetime | None
    latest_ingestion_run_id: str | None
    freshness_lag_seconds: float | None
    freshness_status: str
    rate_limit_limit: int | None = None
    rate_limit_remaining_min: int | None = None
    rate_limit_used_max: int | None = None
    rate_limit_reset_epoch_seconds_max: int | None = None
    rate_limit_resource: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "tenant_id": self.tenant_id,
            "source": self.source,
            "layer": self.layer,
            "resource_type": self.resource_type,
            "table_path": str(self.table_path),
            "table_exists": self.table_exists,
            "row_count": self.row_count,
            "delta_version": self.delta_version,
            "latest_successful_ingestion_at": (
                self.latest_successful_ingestion_at.isoformat()
                if self.latest_successful_ingestion_at
                else None
            ),
            "latest_ingestion_run_id": self.latest_ingestion_run_id,
            "freshness_lag_seconds": self.freshness_lag_seconds,
            "freshness_lag_hours": (
                round(self.freshness_lag_seconds / 3600.0, 6)
                if self.freshness_lag_seconds is not None
                else None
            ),
            "freshness_status": self.freshness_status,
            "rate_limit_limit": self.rate_limit_limit,
            "rate_limit_remaining_min": self.rate_limit_remaining_min,
            "rate_limit_used_max": self.rate_limit_used_max,
            "rate_limit_reset_epoch_seconds_max": self.rate_limit_reset_epoch_seconds_max,
            "rate_limit_resource": self.rate_limit_resource,
        }

    def as_dagster_metadata(self) -> dict[str, Any]:
        """Return compact fields suitable for Dagster materialization metadata."""

        metadata: dict[str, Any] = {
            "table_exists": self.table_exists,
            "observed_row_count": self.row_count,
            "freshness_status": self.freshness_status,
        }
        if self.latest_successful_ingestion_at is not None:
            metadata["latest_successful_ingestion_at"] = (
                self.latest_successful_ingestion_at.isoformat()
            )
        if self.latest_ingestion_run_id:
            metadata["latest_ingestion_run_id"] = self.latest_ingestion_run_id
        if self.freshness_lag_seconds is not None:
            metadata["freshness_lag_seconds"] = round(self.freshness_lag_seconds, 3)
            metadata["freshness_lag_hours"] = round(self.freshness_lag_seconds / 3600.0, 6)
        if self.rate_limit_remaining_min is not None:
            metadata["rate_limit_remaining_min"] = self.rate_limit_remaining_min
        if self.rate_limit_limit is not None:
            metadata["rate_limit_limit"] = self.rate_limit_limit
        if self.rate_limit_reset_epoch_seconds_max is not None:
            metadata["rate_limit_reset_epoch_seconds_max"] = self.rate_limit_reset_epoch_seconds_max
        if self.rate_limit_resource:
            metadata["rate_limit_resource"] = self.rate_limit_resource
        return metadata


GITHUB_TABLE_CONFIGS: tuple[GitHubTableObservabilityConfig, ...] = (
    GitHubTableObservabilityConfig(
        layer="bronze",
        resource_type=REPOSITORY_RESOURCE,
        freshness_column="fetched_at",
        ingestion_run_column="ingestion_run_id",
        rate_limit_column="rate_limit_json",
    ),
    GitHubTableObservabilityConfig(
        layer="bronze",
        resource_type=PULL_REQUEST_RESOURCE,
        freshness_column="fetched_at",
        ingestion_run_column="ingestion_run_id",
        rate_limit_column="rate_limit_json",
    ),
    GitHubTableObservabilityConfig(
        layer="silver",
        resource_type=REPOSITORY_RESOURCE,
        freshness_column="fetched_at",
        ingestion_run_column="ingestion_run_id",
    ),
    GitHubTableObservabilityConfig(
        layer="silver",
        resource_type=PULL_REQUEST_RESOURCE,
        freshness_column="fetched_at",
        ingestion_run_column="ingestion_run_id",
    ),
    GitHubTableObservabilityConfig(
        layer="gold",
        resource_type=PR_THROUGHPUT_DAILY_TABLE,
        freshness_column="latest_fetched_at",
        ingestion_run_column="latest_ingestion_run_id",
    ),
    GitHubTableObservabilityConfig(
        layer="gold",
        resource_type=PR_CYCLE_TIME_TABLE,
        freshness_column="fetched_at",
        ingestion_run_column="ingestion_run_id",
    ),
)


def collect_github_observability(
    *,
    tenant_ids: Sequence[str] | None = None,
    now: datetime | None = None,
    stale_after_hours: float = DEFAULT_STALE_AFTER_HOURS,
) -> list[TableObservability]:
    """Collect local observability summaries for known GitHub tables."""

    registry = load_tenant_registry()
    selected_tenant_ids = tuple(tenant_ids or registry.tenant_ids)
    observed_at = _normalize_datetime(now or datetime.now(tz=UTC))
    return [
        observe_github_table(
            tenant_id=tenant_id,
            config=config,
            now=observed_at,
            stale_after_hours=stale_after_hours,
        )
        for tenant_id in selected_tenant_ids
        for config in GITHUB_TABLE_CONFIGS
    ]


def observe_github_table(
    *,
    tenant_id: str,
    config: GitHubTableObservabilityConfig,
    now: datetime | None = None,
    stale_after_hours: float = DEFAULT_STALE_AFTER_HOURS,
) -> TableObservability:
    """Observe one known tenant-scoped GitHub Delta table."""

    safe_tenant_id = validate_tenant_id(tenant_id)
    observed_at = _normalize_datetime(now or datetime.now(tz=UTC))
    table_path = delta_table_path(
        safe_tenant_id, config.layer, GITHUB_SOURCE, config.resource_type
    )

    if not table_path.exists():
        return TableObservability(
            tenant_id=safe_tenant_id,
            source=GITHUB_SOURCE,
            layer=config.layer,
            resource_type=config.resource_type,
            table_path=table_path,
            table_exists=False,
            row_count=0,
            delta_version=None,
            latest_successful_ingestion_at=None,
            latest_ingestion_run_id=None,
            freshness_lag_seconds=None,
            freshness_status="missing",
        )

    delta_table = DeltaTable(str(table_path))
    rows = delta_table.to_pyarrow_table().to_pylist()
    if not rows:
        return TableObservability(
            tenant_id=safe_tenant_id,
            source=GITHUB_SOURCE,
            layer=config.layer,
            resource_type=config.resource_type,
            table_path=table_path,
            table_exists=True,
            row_count=0,
            delta_version=delta_table.version(),
            latest_successful_ingestion_at=None,
            latest_ingestion_run_id=None,
            freshness_lag_seconds=None,
            freshness_status="empty",
        )

    latest_ingested_at = _latest_datetime(rows, config.freshness_column)
    latest_run_id = _latest_run_id(rows, config.ingestion_run_column, latest_ingested_at)
    lag_seconds = (
        max((observed_at - latest_ingested_at).total_seconds(), 0.0)
        if latest_ingested_at is not None
        else None
    )
    rate_limit_summary = _summarize_rate_limits(rows, config.rate_limit_column)

    return TableObservability(
        tenant_id=safe_tenant_id,
        source=GITHUB_SOURCE,
        layer=config.layer,
        resource_type=config.resource_type,
        table_path=table_path,
        table_exists=True,
        row_count=len(rows),
        delta_version=delta_table.version(),
        latest_successful_ingestion_at=latest_ingested_at,
        latest_ingestion_run_id=latest_run_id,
        freshness_lag_seconds=lag_seconds,
        freshness_status=_freshness_status(lag_seconds, stale_after_hours),
        rate_limit_limit=_summary_int(rate_limit_summary, "limit"),
        rate_limit_remaining_min=_summary_int(rate_limit_summary, "remaining_min"),
        rate_limit_used_max=_summary_int(rate_limit_summary, "used_max"),
        rate_limit_reset_epoch_seconds_max=_summary_int(
            rate_limit_summary, "reset_epoch_seconds_max"
        ),
        rate_limit_resource=_summary_str(rate_limit_summary, "resource"),
    )


def _latest_datetime(rows: Iterable[Mapping[str, Any]], column: str | None) -> datetime | None:
    if column is None:
        return None
    values = [_datetime_or_none(row.get(column)) for row in rows]
    parsed_values = [value for value in values if value is not None]
    if not parsed_values:
        return None
    return max(parsed_values)


def _latest_run_id(
    rows: Iterable[Mapping[str, Any]], column: str | None, latest_at: datetime | None
) -> str | None:
    if column is None:
        return None
    selected: str | None = None
    for row in rows:
        value = row.get(column)
        if not isinstance(value, str) or not value:
            continue
        if latest_at is None:
            selected = value
            continue
        row_timestamp = _first_present_datetime(
            row.get("fetched_at"),
            row.get("latest_fetched_at"),
            row.get("created_at"),
            row.get("metric_date"),
        )
        if row_timestamp is None or row_timestamp == latest_at:
            selected = value
    return selected


def _summarize_rate_limits(
    rows: Iterable[Mapping[str, Any]], column: str | None
) -> dict[str, int | str | None]:
    if column is None:
        return {}
    limits: list[int] = []
    remaining_values: list[int] = []
    used_values: list[int] = []
    reset_values: list[int] = []
    resources: set[str] = set()

    for row in rows:
        raw = row.get(column)
        if not isinstance(raw, str) or not raw:
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        _append_int(limits, parsed.get("limit"))
        _append_int(remaining_values, parsed.get("remaining"))
        _append_int(used_values, parsed.get("used"))
        _append_int(reset_values, parsed.get("reset_epoch_seconds"))
        resource = parsed.get("resource")
        if isinstance(resource, str) and resource:
            resources.add(resource)

    summary: dict[str, int | str | None] = {}
    if limits:
        summary["limit"] = max(limits)
    if remaining_values:
        summary["remaining_min"] = min(remaining_values)
    if used_values:
        summary["used_max"] = max(used_values)
    if reset_values:
        summary["reset_epoch_seconds_max"] = max(reset_values)
    if resources:
        summary["resource"] = ",".join(sorted(resources))
    return summary


def _summary_int(summary: Mapping[str, int | str | None], key: str) -> int | None:
    value = summary.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _summary_str(summary: Mapping[str, int | str | None], key: str) -> str | None:
    value = summary.get(key)
    return value if isinstance(value, str) and value else None


def _append_int(values: list[int], value: object) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int):
        values.append(value)
        return
    if isinstance(value, str):
        try:
            values.append(int(value))
        except ValueError:
            return


def _freshness_status(lag_seconds: float | None, stale_after_hours: float) -> str:
    if lag_seconds is None:
        return "unknown"
    return "fresh" if lag_seconds <= stale_after_hours * 3600.0 else "stale"


def _datetime_or_none(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return _normalize_datetime(value)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str) and value:
        normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
        try:
            return _normalize_datetime(datetime.fromisoformat(normalized))
        except ValueError:
            return None
    return None


def _first_present_datetime(*values: object) -> datetime | None:
    for value in values:
        parsed = _datetime_or_none(value)
        if parsed is not None:
            return parsed
    return None


def _normalize_datetime(value: datetime) -> datetime:
    return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for local GitHub observability."""

    parser = argparse.ArgumentParser(description="Inspect local GitHub Delta observability.")
    parser.add_argument("--tenant", action="append", dest="tenants", help="Tenant ID to inspect.")
    parser.add_argument(
        "--all-tenants", action="store_true", help="Inspect all configured tenants."
    )
    parser.add_argument(
        "--data-root",
        help="Override KABUTO_DATA_ROOT for this run. Useful for temp validation roots.",
    )
    parser.add_argument(
        "--stale-after-hours",
        type=float,
        default=DEFAULT_STALE_AFTER_HOURS,
        help=f"Freshness threshold in hours. Defaults to {DEFAULT_STALE_AFTER_HOURS}.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="json",
        help="Output JSON or a compact terminal table.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entrypoint for local observability inspection."""

    args = parse_args(argv)
    if args.data_root:
        os.environ["KABUTO_DATA_ROOT"] = args.data_root

    registry = load_tenant_registry()
    tenant_ids = tuple(args.tenants or ())
    if args.all_tenants:
        tenant_ids = registry.tenant_ids
    if not tenant_ids:
        raise SystemExit("Pass --tenant TENANT_ID or --all-tenants")

    now = datetime.now(tz=UTC)
    records = collect_github_observability(
        tenant_ids=tenant_ids,
        now=now,
        stale_after_hours=args.stale_after_hours,
    )
    if args.format == "table":
        print(_format_table(records))
        return
    print(
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "data_root": str(data_root()),
                "stale_after_hours": args.stale_after_hours,
                "records": [record.as_dict() for record in records],
            },
            indent=2,
            sort_keys=True,
        )
    )


def _format_table(records: Sequence[TableObservability]) -> str:
    headers = [
        "tenant",
        "layer",
        "resource",
        "rows",
        "freshness",
        "lag_hours",
        "latest_ingested",
        "run_id",
        "rate_remaining",
    ]
    rows = [headers]
    for record in records:
        rows.append(
            [
                record.tenant_id,
                record.layer,
                record.resource_type,
                str(record.row_count),
                record.freshness_status,
                f"{record.freshness_lag_seconds / 3600.0:.2f}"
                if record.freshness_lag_seconds is not None
                else "",
                record.latest_successful_ingestion_at.isoformat()
                if record.latest_successful_ingestion_at
                else "",
                record.latest_ingestion_run_id or "",
                str(record.rate_limit_remaining_min)
                if record.rate_limit_remaining_min is not None
                else "",
            ]
        )
    widths = [max(len(str(row[index])) for row in rows) for index in range(len(headers))]
    lines = []
    for row_index, row in enumerate(rows):
        lines.append("  ".join(str(value).ljust(widths[index]) for index, value in enumerate(row)))
        if row_index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
