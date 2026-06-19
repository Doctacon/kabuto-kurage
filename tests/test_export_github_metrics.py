from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest
from deltalake import write_deltalake

from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.queries.github_metrics import (
    GitHubMetricsQueryError,
    query_pr_cycle_time,
    query_pr_throughput_daily,
    summarize_github_metrics,
)
from kabuto_kurage.tenancy import TenantConfigError
from kabuto_kurage.transforms.github_gold import (
    PR_CYCLE_TIME_SCHEMA,
    PR_CYCLE_TIME_TABLE,
    PR_THROUGHPUT_DAILY_SCHEMA,
    PR_THROUGHPUT_DAILY_TABLE,
)

FETCHED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


def write_gold_rows(
    tenant_id: str,
    *,
    table_name: str,
    schema: pa.Schema,
    rows: list[dict[str, Any]],
) -> None:
    table_path = delta_table_path(tenant_id, "gold", "github", table_name)
    table_path.parent.mkdir(parents=True, exist_ok=True)
    columns = {field.name: [] for field in schema}
    for row in rows:
        for field in schema:
            columns[field.name].append(row.get(field.name))
    write_deltalake(str(table_path), pa.table(columns, schema=schema), mode="overwrite")


def throughput_row(
    *,
    tenant_id: str = "sandbox",
    repository_full_name: str = "octocat/Hello-World",
    metric_date: date = date(2026, 6, 1),
    opened_count: int = 0,
    merged_count: int = 0,
    closed_count: int = 0,
    observed_pull_request_count: int = 1,
    latest_fetched_at: datetime = FETCHED_AT,
    latest_ingestion_run_id: str = "run-sandbox",
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "source": "github",
        "repository_full_name": repository_full_name,
        "metric_date": metric_date,
        "opened_count": opened_count,
        "merged_count": merged_count,
        "closed_count": closed_count,
        "observed_pull_request_count": observed_pull_request_count,
        "latest_fetched_at": latest_fetched_at,
        "latest_ingestion_run_id": latest_ingestion_run_id,
    }


def cycle_time_row(
    *,
    tenant_id: str = "sandbox",
    repository_full_name: str = "octocat/Hello-World",
    number: int = 1,
    created_at: datetime = datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
    merged_at: datetime | None = datetime(2026, 6, 2, 10, 0, tzinfo=UTC),
    merged: bool = True,
    cycle_time_hours: float | None = 24.0,
    fetched_at: datetime = FETCHED_AT,
    ingestion_run_id: str = "run-sandbox",
) -> dict[str, Any]:
    repository_owner = repository_full_name.split("/", 1)[0]
    return {
        "tenant_id": tenant_id,
        "source": "github",
        "repository_full_name": repository_full_name,
        "repository_owner": repository_owner,
        "pull_request_id": number,
        "pull_request_node_id": f"pr-node-{tenant_id}-{number}",
        "number": number,
        "title": f"PR {number}",
        "user_login": "octocat",
        "state": "closed" if merged_at else "open",
        "merged": merged,
        "created_at": created_at,
        "merged_at": merged_at,
        "cycle_time_hours": cycle_time_hours,
        "cycle_time_days": round(cycle_time_hours / 24.0, 6) if cycle_time_hours else None,
        "fetched_at": fetched_at,
        "ingestion_run_id": ingestion_run_id,
    }


@pytest.fixture
def seeded_gold_tables(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    write_gold_rows(
        "sandbox",
        table_name=PR_THROUGHPUT_DAILY_TABLE,
        schema=PR_THROUGHPUT_DAILY_SCHEMA,
        rows=[
            throughput_row(metric_date=date(2026, 6, 1), opened_count=2),
            throughput_row(metric_date=date(2026, 6, 2), merged_count=1, closed_count=1),
            throughput_row(
                repository_full_name="octocat/Spoon-Knife",
                metric_date=date(2026, 6, 3),
                opened_count=1,
                latest_fetched_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            ),
        ],
    )
    write_gold_rows(
        "sandbox",
        table_name=PR_CYCLE_TIME_TABLE,
        schema=PR_CYCLE_TIME_SCHEMA,
        rows=[
            cycle_time_row(number=1),
            cycle_time_row(
                number=2,
                created_at=datetime(2026, 6, 2, 10, 0, tzinfo=UTC),
                merged_at=datetime(2026, 6, 3, 22, 0, tzinfo=UTC),
                cycle_time_hours=36.0,
            ),
            cycle_time_row(
                number=3,
                created_at=datetime(2026, 6, 3, 10, 0, tzinfo=UTC),
                merged_at=None,
                merged=False,
                cycle_time_hours=None,
            ),
            cycle_time_row(
                repository_full_name="octocat/Spoon-Knife",
                number=4,
                created_at=datetime(2026, 6, 4, 10, 0, tzinfo=UTC),
                merged_at=datetime(2026, 6, 5, 10, 0, tzinfo=UTC),
                cycle_time_hours=24.0,
                fetched_at=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
            ),
        ],
    )
    write_gold_rows(
        "personal",
        table_name=PR_THROUGHPUT_DAILY_TABLE,
        schema=PR_THROUGHPUT_DAILY_SCHEMA,
        rows=[
            throughput_row(
                tenant_id="personal",
                repository_full_name="crlough/kabuto-kurage",
                metric_date=date(2026, 7, 1),
                opened_count=1,
                latest_ingestion_run_id="run-personal",
            )
        ],
    )
    write_gold_rows(
        "personal",
        table_name=PR_CYCLE_TIME_TABLE,
        schema=PR_CYCLE_TIME_SCHEMA,
        rows=[
            cycle_time_row(
                tenant_id="personal",
                repository_full_name="crlough/kabuto-kurage",
                number=7,
                created_at=datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
                ingestion_run_id="run-personal",
            )
        ],
    )
    return tmp_path


def assert_no_raw_or_secret_fields(records: list[dict[str, Any]]) -> None:
    for record in records:
        assert "payload_json" not in record
        assert "source" not in record
        assert all("token" not in key.lower() for key in record)
        assert all(value != "ghp_secret_should_not_appear" for value in record.values())


def test_query_pr_throughput_daily_filters_date_repository_limit_and_offset(
    seeded_gold_tables: Path,
) -> None:
    records = query_pr_throughput_daily(
        "sandbox",
        start_date="2026-06-01",
        end_date="2026-06-02",
        repository_full_names="octocat/Hello-World",
        limit=1,
        offset=1,
    )

    assert records == [
        {
            "tenant_id": "sandbox",
            "repository_full_name": "octocat/Hello-World",
            "metric_date": "2026-06-02",
            "opened_count": 0,
            "merged_count": 1,
            "closed_count": 1,
            "observed_pull_request_count": 1,
            "latest_fetched_at": "2026-06-18T12:00:00+00:00",
            "latest_ingestion_run_id": "run-sandbox",
        }
    ]
    json.dumps(records)
    assert_no_raw_or_secret_fields(records)


def test_query_pr_cycle_time_filters_date_repository_merged_limit_and_offset(
    seeded_gold_tables: Path,
) -> None:
    records = query_pr_cycle_time(
        "sandbox",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 3),
        repository_full_names=["octocat/Hello-World"],
        merged=True,
        limit=1,
        offset=1,
    )

    assert len(records) == 1
    assert records[0]["tenant_id"] == "sandbox"
    assert records[0]["repository_full_name"] == "octocat/Hello-World"
    assert records[0]["number"] == 2
    assert records[0]["created_at"] == "2026-06-02T10:00:00+00:00"
    assert records[0]["cycle_time_hours"] == 36.0
    json.dumps(records)
    assert_no_raw_or_secret_fields(records)


def test_summarize_github_metrics_from_filtered_gold_tables(seeded_gold_tables: Path) -> None:
    summary = summarize_github_metrics(
        "sandbox",
        start_date="2026-06-01",
        end_date="2026-06-03",
        repository_full_names=["octocat/Hello-World"],
    )

    assert summary.as_dict() == {
        "tenant_id": "sandbox",
        "repositories_observed": 1,
        "opened_count": 2,
        "merged_count": 1,
        "closed_count": 1,
        "pull_requests_observed": 3,
        "merged_pull_requests_observed": 2,
        "average_cycle_time_hours": 30.0,
        "latest_fetched_at": "2026-06-18T12:00:00+00:00",
    }
    json.dumps(summary.as_dict())


def test_queries_use_tenant_scoped_gold_paths_without_cross_tenant_rows(
    seeded_gold_tables: Path,
) -> None:
    sandbox_records = query_pr_cycle_time("sandbox", limit=None)
    personal_records = query_pr_cycle_time("personal", limit=None)

    assert {record["tenant_id"] for record in sandbox_records} == {"sandbox"}
    assert {record["repository_full_name"] for record in sandbox_records} == {
        "octocat/Hello-World",
        "octocat/Spoon-Knife",
    }
    assert personal_records == [
        {
            **personal_records[0],
            "tenant_id": "personal",
            "repository_full_name": "crlough/kabuto-kurage",
            "number": 7,
        }
    ]
    assert_no_raw_or_secret_fields(sandbox_records)
    assert_no_raw_or_secret_fields(personal_records)


def test_query_validation_fails_for_invalid_tenant_id_and_missing_gold_tables(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))

    with pytest.raises(TenantConfigError, match="tenant_id must"):
        query_pr_throughput_daily("BadTenant")

    with pytest.raises(GitHubMetricsQueryError, match="Gold GitHub pr_throughput_daily table"):
        query_pr_throughput_daily("sandbox")

    write_gold_rows(
        "sandbox",
        table_name=PR_THROUGHPUT_DAILY_TABLE,
        schema=PR_THROUGHPUT_DAILY_SCHEMA,
        rows=[throughput_row()],
    )
    with pytest.raises(GitHubMetricsQueryError, match="Gold GitHub pr_cycle_time table"):
        query_pr_cycle_time("sandbox")


def test_query_rejects_mismatched_tenant_rows_in_gold_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    write_gold_rows(
        "sandbox",
        table_name=PR_THROUGHPUT_DAILY_TABLE,
        schema=PR_THROUGHPUT_DAILY_SCHEMA,
        rows=[throughput_row(tenant_id="personal", repository_full_name="crlough/kabuto-kurage")],
    )

    with pytest.raises(GitHubMetricsQueryError, match="found rows for tenant_id"):
        query_pr_throughput_daily("sandbox")
