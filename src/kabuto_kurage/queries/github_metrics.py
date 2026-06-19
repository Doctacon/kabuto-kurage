"""Shared tenant-scoped DuckDB query layer for GitHub gold engineering metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TypeAlias

import duckdb

from kabuto_kurage.ingestion.github_bronze import GITHUB_SOURCE
from kabuto_kurage.paths import active_storage_profile, duckdb_delta_table_uri
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

    Dates are inclusive filters on ``metric_date``. DuckDB executes filtering,
    ordering, limit, and offset directly against the tenant-scoped Delta table.
    Returned records intentionally expose only export-contract fields, excluding
    internal fields such as ``source``.
    """

    safe_tenant_id = validate_tenant_id(tenant_id)
    normalized_start_date = _normalize_date(start_date, field="start_date")
    normalized_end_date = _normalize_date(end_date, field="end_date")
    repositories = _normalize_repositories(repository_full_names)
    _validate_date_order(normalized_start_date, normalized_end_date)
    normalized_offset = _normalize_offset(offset)
    normalized_limit = None if limit is None else _normalize_limit(limit)

    table_uri = _gold_table_uri(safe_tenant_id, PR_THROUGHPUT_DAILY_TABLE)
    with _duckdb_connection() as conn:
        _require_delta_table(
            conn, table_uri, tenant_id=safe_tenant_id, table_name=PR_THROUGHPUT_DAILY_TABLE
        )
        _validate_table_rows_belong_to_tenant(
            conn, table_uri, tenant_id=safe_tenant_id, table_name=PR_THROUGHPUT_DAILY_TABLE
        )
        where_sql, params = _throughput_where_clause(
            safe_tenant_id,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
            repositories=repositories,
        )
        query = f"""
            SELECT
                tenant_id,
                repository_full_name,
                metric_date,
                opened_count,
                merged_count,
                closed_count,
                observed_pull_request_count,
                latest_fetched_at,
                latest_ingestion_run_id
            FROM delta_scan(?)
            {where_sql}
            ORDER BY metric_date, repository_full_name
            {_limit_offset_sql(normalized_limit)}
            OFFSET ?
        """
        rows = _fetch_dict_rows(
            conn,
            query,
            [table_uri, *params, *_limit_params(normalized_limit), normalized_offset],
        )

    return [_serialize_record(row, THROUGHPUT_DAILY_FIELDS) for row in rows]


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

    Dates are inclusive filters on the PR ``created_at`` date. DuckDB executes
    filtering, ordering, limit, and offset directly against the tenant-scoped
    Delta table. Returned records intentionally expose only export-contract
    fields, excluding internal fields such as ``source``.
    """

    safe_tenant_id = validate_tenant_id(tenant_id)
    normalized_start_date = _normalize_date(start_date, field="start_date")
    normalized_end_date = _normalize_date(end_date, field="end_date")
    repositories = _normalize_repositories(repository_full_names)
    _validate_date_order(normalized_start_date, normalized_end_date)
    normalized_offset = _normalize_offset(offset)
    normalized_limit = None if limit is None else _normalize_limit(limit)

    table_uri = _gold_table_uri(safe_tenant_id, PR_CYCLE_TIME_TABLE)
    with _duckdb_connection() as conn:
        _require_delta_table(
            conn, table_uri, tenant_id=safe_tenant_id, table_name=PR_CYCLE_TIME_TABLE
        )
        _validate_table_rows_belong_to_tenant(
            conn, table_uri, tenant_id=safe_tenant_id, table_name=PR_CYCLE_TIME_TABLE
        )
        where_sql, params = _cycle_time_where_clause(
            safe_tenant_id,
            start_date=normalized_start_date,
            end_date=normalized_end_date,
            repositories=repositories,
            merged=merged,
        )
        query = f"""
            SELECT
                tenant_id,
                repository_full_name,
                repository_owner,
                pull_request_id,
                pull_request_node_id,
                number,
                title,
                user_login,
                state,
                merged,
                created_at,
                merged_at,
                cycle_time_hours,
                cycle_time_days,
                fetched_at,
                ingestion_run_id
            FROM delta_scan(?)
            {where_sql}
            ORDER BY created_at, repository_full_name, number
            {_limit_offset_sql(normalized_limit)}
            OFFSET ?
        """
        rows = _fetch_dict_rows(
            conn,
            query,
            [table_uri, *params, *_limit_params(normalized_limit), normalized_offset],
        )

    return [_serialize_record(row, CYCLE_TIME_FIELDS) for row in rows]


def summarize_github_metrics(
    tenant_id: str,
    *,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_names: RepositoryFilter = None,
) -> GitHubMetricsSummary:
    """Produce a compact tenant-scoped summary from existing GitHub gold tables.

    DuckDB computes the throughput, cycle-time, repository, and freshness
    aggregations directly over tenant-scoped Delta gold tables.
    """

    safe_tenant_id = validate_tenant_id(tenant_id)
    normalized_start_date = _normalize_date(start_date, field="start_date")
    normalized_end_date = _normalize_date(end_date, field="end_date")
    repositories = _normalize_repositories(repository_full_names)
    _validate_date_order(normalized_start_date, normalized_end_date)

    throughput_uri = _gold_table_uri(safe_tenant_id, PR_THROUGHPUT_DAILY_TABLE)
    cycle_time_uri = _gold_table_uri(safe_tenant_id, PR_CYCLE_TIME_TABLE)
    throughput_where, throughput_params = _throughput_where_clause(
        safe_tenant_id,
        start_date=normalized_start_date,
        end_date=normalized_end_date,
        repositories=repositories,
        table_alias="t",
    )
    cycle_time_where, cycle_time_params = _cycle_time_where_clause(
        safe_tenant_id,
        start_date=normalized_start_date,
        end_date=normalized_end_date,
        repositories=repositories,
        merged=None,
        table_alias="c",
    )

    with _duckdb_connection() as conn:
        _require_delta_table(
            conn, throughput_uri, tenant_id=safe_tenant_id, table_name=PR_THROUGHPUT_DAILY_TABLE
        )
        _require_delta_table(
            conn, cycle_time_uri, tenant_id=safe_tenant_id, table_name=PR_CYCLE_TIME_TABLE
        )
        _validate_table_rows_belong_to_tenant(
            conn, throughput_uri, tenant_id=safe_tenant_id, table_name=PR_THROUGHPUT_DAILY_TABLE
        )
        _validate_table_rows_belong_to_tenant(
            conn, cycle_time_uri, tenant_id=safe_tenant_id, table_name=PR_CYCLE_TIME_TABLE
        )
        query = f"""
            WITH
            t AS (
                SELECT *
                FROM delta_scan(?) AS t
                {throughput_where}
            ),
            c AS (
                SELECT *
                FROM delta_scan(?) AS c
                {cycle_time_where}
            ),
            repos AS (
                SELECT repository_full_name FROM t WHERE repository_full_name IS NOT NULL
                UNION
                SELECT repository_full_name FROM c WHERE repository_full_name IS NOT NULL
            ),
            fetched AS (
                SELECT latest_fetched_at AS fetched_at FROM t WHERE latest_fetched_at IS NOT NULL
                UNION ALL
                SELECT fetched_at FROM c WHERE fetched_at IS NOT NULL
            )
            SELECT
                (SELECT count(*) FROM repos) AS repositories_observed,
                (SELECT coalesce(sum(opened_count), 0) FROM t) AS opened_count,
                (SELECT coalesce(sum(merged_count), 0) FROM t) AS merged_count,
                (SELECT coalesce(sum(closed_count), 0) FROM t) AS closed_count,
                (SELECT count(*) FROM c) AS pull_requests_observed,
                (SELECT count(*) FROM c WHERE merged IS TRUE) AS merged_pull_requests_observed,
                (SELECT avg(cycle_time_hours) FROM c WHERE cycle_time_hours IS NOT NULL)
                    AS average_cycle_time_hours,
                (SELECT max(fetched_at) FROM fetched) AS latest_fetched_at
        """
        rows = _fetch_dict_rows(
            conn,
            query,
            [throughput_uri, *throughput_params, cycle_time_uri, *cycle_time_params],
        )

    summary_row = rows[0] if rows else {}
    average_cycle_time_hours = _float_or_none(summary_row.get("average_cycle_time_hours"))
    return GitHubMetricsSummary(
        tenant_id=safe_tenant_id,
        repositories_observed=_int_value(summary_row.get("repositories_observed")),
        opened_count=_int_value(summary_row.get("opened_count")),
        merged_count=_int_value(summary_row.get("merged_count")),
        closed_count=_int_value(summary_row.get("closed_count")),
        pull_requests_observed=_int_value(summary_row.get("pull_requests_observed")),
        merged_pull_requests_observed=_int_value(
            summary_row.get("merged_pull_requests_observed")
        ),
        average_cycle_time_hours=(
            round(average_cycle_time_hours, 6) if average_cycle_time_hours is not None else None
        ),
        latest_fetched_at=_serialize_timestamp_or_none(summary_row.get("latest_fetched_at")),
    )


def query_backend_summary() -> JsonObject:
    """Return non-secret details about the export query backend."""

    profile = active_storage_profile()
    return {
        "engine": "duckdb",
        "delta_scan": True,
        "storage_profile": profile.name,
    }


def serialize_json_value(value: object) -> JsonValue:
    """Serialize Python/DuckDB scalar values returned by queries into JSON-safe values."""

    return _serialize_value(value)


def _duckdb_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:")
    profile = active_storage_profile()
    try:
        for statement in profile.duckdb_secret_sql(include_secrets=not profile.is_local):
            conn.execute(statement)
    except Exception:
        conn.close()
        raise
    return conn


def _gold_table_uri(tenant_id: str, table_name: str) -> str:
    return duckdb_delta_table_uri(tenant_id, "gold", GITHUB_SOURCE, table_name)


def _require_delta_table(
    conn: duckdb.DuckDBPyConnection, table_uri: str, *, tenant_id: str, table_name: str
) -> None:
    try:
        conn.execute("SELECT 1 FROM delta_scan(?) LIMIT 1", [table_uri]).fetchall()
    except duckdb.Error as exc:
        raise GitHubMetricsQueryError(
            f"Gold GitHub {table_name} table does not exist for tenant {tenant_id}: {table_uri}"
        ) from exc


def _validate_table_rows_belong_to_tenant(
    conn: duckdb.DuckDBPyConnection, table_uri: str, *, tenant_id: str, table_name: str
) -> None:
    rows = conn.execute(
        """
        SELECT DISTINCT tenant_id
        FROM delta_scan(?)
        WHERE tenant_id IS DISTINCT FROM ?
        ORDER BY tenant_id
        """,
        [table_uri, tenant_id],
    ).fetchall()
    mismatched_tenant_ids = [str(row[0]) for row in rows]
    if mismatched_tenant_ids:
        raise GitHubMetricsQueryError(
            f"Refusing to export tenant {tenant_id} gold/{table_name}: "
            f"found rows for tenant_id values {mismatched_tenant_ids}"
        )


def _throughput_where_clause(
    tenant_id: str,
    *,
    start_date: date | None,
    end_date: date | None,
    repositories: tuple[str, ...] | None,
    table_alias: str | None = None,
) -> tuple[str, list[object]]:
    prefix = f"{table_alias}." if table_alias else ""
    conditions = [f"{prefix}tenant_id = ?"]
    params: list[object] = [tenant_id]
    if start_date is not None:
        conditions.append(f"{prefix}metric_date >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append(f"{prefix}metric_date <= ?")
        params.append(end_date)
    if repositories is not None:
        placeholders = ", ".join("?" for _ in repositories)
        conditions.append(f"{prefix}repository_full_name IN ({placeholders})")
        params.extend(repositories)
    return f"WHERE {' AND '.join(conditions)}", params


def _cycle_time_where_clause(
    tenant_id: str,
    *,
    start_date: date | None,
    end_date: date | None,
    repositories: tuple[str, ...] | None,
    merged: bool | None,
    table_alias: str | None = None,
) -> tuple[str, list[object]]:
    prefix = f"{table_alias}." if table_alias else ""
    conditions = [f"{prefix}tenant_id = ?"]
    params: list[object] = [tenant_id]
    if start_date is not None:
        conditions.append(f"CAST({prefix}created_at AS DATE) >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append(f"CAST({prefix}created_at AS DATE) <= ?")
        params.append(end_date)
    if repositories is not None:
        placeholders = ", ".join("?" for _ in repositories)
        conditions.append(f"{prefix}repository_full_name IN ({placeholders})")
        params.extend(repositories)
    if merged is not None:
        conditions.append(f"{prefix}merged = ?")
        params.append(merged)
    return f"WHERE {' AND '.join(conditions)}", params


def _limit_offset_sql(limit: int | None) -> str:
    if limit is None:
        return ""
    return "LIMIT ?"


def _limit_params(limit: int | None) -> list[object]:
    if limit is None:
        return []
    return [limit]


def _fetch_dict_rows(
    conn: duckdb.DuckDBPyConnection, query: str, params: Sequence[object]
) -> list[dict[str, object]]:
    cursor = conn.execute(query, list(params))
    column_names = [column[0] for column in cursor.description]
    return [dict(zip(column_names, row, strict=True)) for row in cursor.fetchall()]


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


def _normalize_repositories(repository_full_names: RepositoryFilter) -> tuple[str, ...] | None:
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
    return repositories


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


def _serialize_record(row: Mapping[str, object], fields: Sequence[str]) -> JsonObject:
    return {field: _serialize_value(row.get(field)) for field in fields}


def _serialize_value(value: object) -> JsonValue:
    if value is None or isinstance(value, str | bool | int | float):
        return value
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat() if value.tzinfo is not None else value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _serialize_value(nested_value) for key, nested_value in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_serialize_value(item) for item in value]
    return str(value)


def _serialize_timestamp_or_none(value: object) -> str | None:
    serialized = _serialize_value(value)
    return serialized if isinstance(serialized, str) else None


def _float_or_none(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0
