"""Shared tenant-scoped query layer for GitHub gold engineering metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, TypeAlias, cast

from deltalake import DeltaTable

from kabuto_kurage.ingestion.github_bronze import GITHUB_SOURCE
from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.tenancy import validate_tenant_id
from kabuto_kurage.transforms.github_gold import PR_CYCLE_TIME_TABLE, PR_THROUGHPUT_DAILY_TABLE

JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]
DateFilter: TypeAlias = date | datetime | str | None
RepositoryFilter: TypeAlias = str | Sequence[str] | None

DEFAULT_EXPORT_LIMIT = 100
MAX_EXPORT_LIMIT = 1_000

THROUGHPUT_DAILY_FIELDS = (
    "tenant_id",
    "repository_full_name",
    "metric_date",
    "opened_count",
    "merged_count",
    "closed_count",
    "observed_pull_request_count",
    "latest_fetched_at",
    "latest_ingestion_run_id",
)

CYCLE_TIME_FIELDS = (
    "tenant_id",
    "repository_full_name",
    "repository_owner",
    "pull_request_id",
    "pull_request_node_id",
    "number",
    "title",
    "user_login",
    "state",
    "merged",
    "created_at",
    "merged_at",
    "cycle_time_hours",
    "cycle_time_days",
    "fetched_at",
    "ingestion_run_id",
)


class GitHubMetricsQueryError(RuntimeError):
    """Raised when tenant-scoped GitHub gold metric queries cannot proceed."""


@dataclass(frozen=True)
class GitHubMetricsSummary:
    """Compact JSON-serializable summary across GitHub gold metric tables."""

    tenant_id: str
    repositories_observed: int
    opened_count: int
    merged_count: int
    closed_count: int
    pull_requests_observed: int
    merged_pull_requests_observed: int
    average_cycle_time_hours: float | None
    latest_fetched_at: str | None

    def as_dict(self) -> JsonObject:
        """Return this summary as a JSON-serializable mapping."""

        return {
            "tenant_id": self.tenant_id,
            "repositories_observed": self.repositories_observed,
            "opened_count": self.opened_count,
            "merged_count": self.merged_count,
            "closed_count": self.closed_count,
            "pull_requests_observed": self.pull_requests_observed,
            "merged_pull_requests_observed": self.merged_pull_requests_observed,
            "average_cycle_time_hours": self.average_cycle_time_hours,
            "latest_fetched_at": self.latest_fetched_at,
        }


def query_pr_throughput_daily(
    tenant_id: str,
    *,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_names: RepositoryFilter = None,
    limit: int | None = DEFAULT_EXPORT_LIMIT,
    offset: int = 0,
) -> list[JsonObject]:
    """Return tenant-scoped daily PR throughput rows from gold Delta tables.

    Dates are inclusive filters on ``metric_date``. Returned records intentionally expose
    only export-contract fields, excluding internal fields such as ``source``.
    """

    safe_tenant_id = validate_tenant_id(tenant_id)
    rows = _filter_throughput_rows(
        _read_gold_rows(safe_tenant_id, PR_THROUGHPUT_DAILY_TABLE),
        start_date=start_date,
        end_date=end_date,
        repository_full_names=repository_full_names,
    )
    return [
        _serialize_record(row, THROUGHPUT_DAILY_FIELDS)
        for row in _paginate(rows, limit=limit, offset=offset)
    ]


def query_pr_cycle_time(
    tenant_id: str,
    *,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_names: RepositoryFilter = None,
    merged: bool | None = None,
    limit: int | None = DEFAULT_EXPORT_LIMIT,
    offset: int = 0,
) -> list[JsonObject]:
    """Return tenant-scoped per-PR cycle-time rows from gold Delta tables.

    Dates are inclusive filters on the PR ``created_at`` date. Returned records
    intentionally expose only export-contract fields, excluding internal fields such as
    ``source``.
    """

    safe_tenant_id = validate_tenant_id(tenant_id)
    rows = _filter_cycle_time_rows(
        _read_gold_rows(safe_tenant_id, PR_CYCLE_TIME_TABLE),
        start_date=start_date,
        end_date=end_date,
        repository_full_names=repository_full_names,
        merged=merged,
    )
    return [
        _serialize_record(row, CYCLE_TIME_FIELDS)
        for row in _paginate(rows, limit=limit, offset=offset)
    ]


def summarize_github_metrics(
    tenant_id: str,
    *,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_names: RepositoryFilter = None,
) -> GitHubMetricsSummary:
    """Produce a compact tenant-scoped summary from existing GitHub gold tables."""

    safe_tenant_id = validate_tenant_id(tenant_id)
    throughput_rows = _filter_throughput_rows(
        _read_gold_rows(safe_tenant_id, PR_THROUGHPUT_DAILY_TABLE),
        start_date=start_date,
        end_date=end_date,
        repository_full_names=repository_full_names,
    )
    cycle_time_rows = _filter_cycle_time_rows(
        _read_gold_rows(safe_tenant_id, PR_CYCLE_TIME_TABLE),
        start_date=start_date,
        end_date=end_date,
        repository_full_names=repository_full_names,
        merged=None,
    )

    cycle_time_values = [
        value for row in cycle_time_rows if isinstance(value := row.get("cycle_time_hours"), float)
    ]
    latest_fetched_values = [
        timestamp
        for row in [*throughput_rows, *cycle_time_rows]
        if isinstance(
            timestamp := _coerce_datetime(row.get("latest_fetched_at") or row.get("fetched_at")),
            datetime,
        )
    ]

    average_cycle_time_hours = None
    if cycle_time_values:
        average_cycle_time_hours = round(sum(cycle_time_values) / len(cycle_time_values), 6)

    latest_fetched_at = max(latest_fetched_values).isoformat() if latest_fetched_values else None

    return GitHubMetricsSummary(
        tenant_id=safe_tenant_id,
        repositories_observed=len(
            {
                repository
                for row in [*throughput_rows, *cycle_time_rows]
                if isinstance(repository := row.get("repository_full_name"), str) and repository
            }
        ),
        opened_count=sum(_int_value(row.get("opened_count")) for row in throughput_rows),
        merged_count=sum(_int_value(row.get("merged_count")) for row in throughput_rows),
        closed_count=sum(_int_value(row.get("closed_count")) for row in throughput_rows),
        pull_requests_observed=len(cycle_time_rows),
        merged_pull_requests_observed=sum(
            1 for row in cycle_time_rows if row.get("merged") is True
        ),
        average_cycle_time_hours=average_cycle_time_hours,
        latest_fetched_at=latest_fetched_at,
    )


def serialize_json_value(value: object) -> JsonValue:
    """Serialize Python/Arrow scalar values returned by Delta into JSON-safe values."""

    return _serialize_value(value)


def _read_gold_rows(tenant_id: str, table_name: str) -> list[dict[str, Any]]:
    table_path = delta_table_path(tenant_id, "gold", GITHUB_SOURCE, table_name)
    _require_delta_table(table_path, tenant_id=tenant_id, table_name=table_name)
    rows = DeltaTable(str(table_path)).to_pyarrow_table().to_pylist()
    typed_rows = cast(list[dict[str, Any]], rows)
    _validate_rows_belong_to_tenant(typed_rows, tenant_id=tenant_id, table_name=table_name)
    return typed_rows


def _require_delta_table(table_path: Path, *, tenant_id: str, table_name: str) -> None:
    if not (table_path / "_delta_log").exists():
        raise GitHubMetricsQueryError(
            f"Gold GitHub {table_name} table does not exist for tenant {tenant_id}: {table_path}"
        )


def _validate_rows_belong_to_tenant(
    rows: Sequence[Mapping[str, Any]], *, tenant_id: str, table_name: str
) -> None:
    mismatched_tenant_ids = sorted(
        {str(row.get("tenant_id")) for row in rows if row.get("tenant_id") != tenant_id}
    )
    if mismatched_tenant_ids:
        raise GitHubMetricsQueryError(
            f"Refusing to export tenant {tenant_id} gold/{table_name}: "
            f"found rows for tenant_id values {mismatched_tenant_ids}"
        )


def _filter_throughput_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    start_date: DateFilter,
    end_date: DateFilter,
    repository_full_names: RepositoryFilter,
) -> list[Mapping[str, Any]]:
    normalized_start_date = _normalize_date(start_date, field="start_date")
    normalized_end_date = _normalize_date(end_date, field="end_date")
    repositories = _normalize_repositories(repository_full_names)
    _validate_date_order(normalized_start_date, normalized_end_date)

    filtered = [
        row
        for row in rows
        if _date_in_range(
            _normalize_date(row.get("metric_date"), field="metric_date"),
            start_date=normalized_start_date,
            end_date=normalized_end_date,
        )
        and _repository_matches(row, repositories)
    ]
    return sorted(
        filtered,
        key=lambda row: (
            str(row.get("metric_date") or ""),
            str(row.get("repository_full_name") or ""),
        ),
    )


def _filter_cycle_time_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    start_date: DateFilter,
    end_date: DateFilter,
    repository_full_names: RepositoryFilter,
    merged: bool | None,
) -> list[Mapping[str, Any]]:
    normalized_start_date = _normalize_date(start_date, field="start_date")
    normalized_end_date = _normalize_date(end_date, field="end_date")
    repositories = _normalize_repositories(repository_full_names)
    _validate_date_order(normalized_start_date, normalized_end_date)

    filtered = [
        row
        for row in rows
        if _date_in_range(
            _normalize_date(row.get("created_at"), field="created_at"),
            start_date=normalized_start_date,
            end_date=normalized_end_date,
        )
        and _repository_matches(row, repositories)
        and (merged is None or row.get("merged") is merged)
    ]
    return sorted(
        filtered,
        key=lambda row: (
            str(row.get("created_at") or ""),
            str(row.get("repository_full_name") or ""),
            _int_value(row.get("number")),
        ),
    )


def _normalize_date(value: object, *, field: str) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise GitHubMetricsQueryError(f"{field} must be an ISO date YYYY-MM-DD") from exc
    raise GitHubMetricsQueryError(f"{field} must be a date, datetime, ISO date string, or None")


def _validate_date_order(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise GitHubMetricsQueryError("end_date must be greater than or equal to start_date")


def _date_in_range(value: date | None, *, start_date: date | None, end_date: date | None) -> bool:
    if value is None:
        return False
    if start_date is not None and value < start_date:
        return False
    if end_date is not None and value > end_date:
        return False
    return True


def _normalize_repositories(repository_full_names: RepositoryFilter) -> frozenset[str] | None:
    if repository_full_names is None:
        return None
    repositories: tuple[str, ...]
    if isinstance(repository_full_names, str):
        repositories = (repository_full_names,)
    else:
        repositories = tuple(repository_full_names)
    if not repositories:
        return None
    if not all(isinstance(repository, str) and repository for repository in repositories):
        raise GitHubMetricsQueryError("repository_full_names must contain only non-empty strings")
    return frozenset(repositories)


def _repository_matches(row: Mapping[str, Any], repositories: frozenset[str] | None) -> bool:
    if repositories is None:
        return True
    repository_full_name = row.get("repository_full_name")
    return isinstance(repository_full_name, str) and repository_full_name in repositories


def _paginate(
    rows: Sequence[Mapping[str, Any]], *, limit: int | None, offset: int
) -> Sequence[Mapping[str, Any]]:
    normalized_offset = _normalize_offset(offset)
    if limit is None:
        return rows[normalized_offset:]
    normalized_limit = _normalize_limit(limit)
    return rows[normalized_offset : normalized_offset + normalized_limit]


def _normalize_limit(limit: int) -> int:
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise GitHubMetricsQueryError("limit must be a positive integer")
    if limit > MAX_EXPORT_LIMIT:
        raise GitHubMetricsQueryError(f"limit must be less than or equal to {MAX_EXPORT_LIMIT}")
    return limit


def _normalize_offset(offset: int) -> int:
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise GitHubMetricsQueryError("offset must be a non-negative integer")
    return offset


def _serialize_record(row: Mapping[str, Any], fields: Sequence[str]) -> JsonObject:
    return {field: _serialize_value(row.get(field)) for field in fields}


def _serialize_value(value: object) -> JsonValue:
    if value is None or isinstance(value, str | bool | int | float):
        return value
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _serialize_value(nested_value) for key, nested_value in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_serialize_value(item) for item in value]
    return str(value)


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    return 0
