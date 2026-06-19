from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.transforms.github_gold import (
    PR_CYCLE_TIME_SCHEMA,
    PR_CYCLE_TIME_TABLE,
    PR_THROUGHPUT_DAILY_SCHEMA,
    PR_THROUGHPUT_DAILY_TABLE,
    compute_pr_cycle_time,
    compute_pr_throughput_daily,
    materialize_tenant_github_gold,
)
from kabuto_kurage.transforms.github_silver import PULL_REQUESTS_SILVER_SCHEMA

FETCHED_AT = datetime(2026, 6, 18, 12, 0, 0, tzinfo=UTC)


def silver_pull_request_row(
    *,
    tenant_id: str = "sandbox",
    repository_full_name: str = "octocat/Hello-World",
    number: int = 1,
    created_at: datetime | None = datetime(2026, 6, 1, 10, 0, tzinfo=UTC),
    closed_at: datetime | None = datetime(2026, 6, 2, 10, 0, tzinfo=UTC),
    merged_at: datetime | None = datetime(2026, 6, 2, 10, 0, tzinfo=UTC),
    merged: bool = True,
) -> dict[str, object]:
    owner = repository_full_name.split("/", 1)[0]
    return {
        "tenant_id": tenant_id,
        "source": "github",
        "pull_request_id": number,
        "pull_request_node_id": f"pr-node-{tenant_id}-{number}",
        "repository_full_name": repository_full_name,
        "repository_owner": owner,
        "number": number,
        "state": "closed" if closed_at else "open",
        "title": f"PR {number}",
        "user_login": "octocat",
        "author_association": "OWNER",
        "draft": False,
        "merged": merged,
        "created_at": created_at,
        "updated_at": created_at,
        "closed_at": closed_at,
        "merged_at": merged_at,
        "html_url": f"https://github.com/{repository_full_name}/pull/{number}",
        "api_url": f"https://api.github.com/repos/{repository_full_name}/pulls/{number}",
        "base_ref": "main",
        "head_ref": f"feature/{number}",
        "base_repo_full_name": repository_full_name,
        "head_repo_full_name": repository_full_name,
        "fetched_at": FETCHED_AT,
        "ingestion_run_id": "run-123",
        "bronze_source_id": f"pr-node-{tenant_id}-{number}",
        "bronze_source_url": f"https://github.com/{repository_full_name}/pull/{number}",
        "bronze_api_url": f"https://api.github.com/repos/{repository_full_name}/pulls/{number}",
    }


def write_silver_pull_requests(tenant_id: str, rows: list[dict[str, object]]) -> None:
    table_path = delta_table_path(tenant_id, "silver", "github", "pull_requests")
    table_path.parent.mkdir(parents=True, exist_ok=True)
    columns = {field.name: [] for field in PULL_REQUESTS_SILVER_SCHEMA}
    for row in rows:
        for field in PULL_REQUESTS_SILVER_SCHEMA:
            columns[field.name].append(row.get(field.name))
    write_deltalake(
        str(table_path), pa.table(columns, schema=PULL_REQUESTS_SILVER_SCHEMA), mode="overwrite"
    )


def test_pr_throughput_daily_counts_opened_merged_and_closed_events() -> None:
    rows = [
        silver_pull_request_row(number=1),
        silver_pull_request_row(number=2, created_at=datetime(2026, 6, 1, 12, 0, tzinfo=UTC)),
        silver_pull_request_row(
            number=3,
            created_at=datetime(2026, 6, 3, 9, 0, tzinfo=UTC),
            closed_at=None,
            merged_at=None,
            merged=False,
        ),
    ]

    metric_rows = compute_pr_throughput_daily(rows)

    by_date = {row["metric_date"].isoformat(): row for row in metric_rows}
    assert by_date["2026-06-01"]["opened_count"] == 2
    assert by_date["2026-06-01"]["merged_count"] == 0
    assert by_date["2026-06-01"]["closed_count"] == 0
    assert by_date["2026-06-01"]["observed_pull_request_count"] == 2
    assert by_date["2026-06-02"]["opened_count"] == 0
    assert by_date["2026-06-02"]["merged_count"] == 2
    assert by_date["2026-06-02"]["closed_count"] == 2
    assert by_date["2026-06-03"]["opened_count"] == 1
    assert by_date["2026-06-03"]["observed_pull_request_count"] == 1
    assert all(row["tenant_id"] == "sandbox" for row in metric_rows)


def test_pr_cycle_time_computes_open_to_merge_duration() -> None:
    rows = [
        silver_pull_request_row(number=1),
        silver_pull_request_row(
            number=2,
            created_at=datetime(2026, 6, 3, 9, 0, tzinfo=UTC),
            closed_at=None,
            merged_at=None,
            merged=False,
        ),
    ]

    cycle_rows = compute_pr_cycle_time(rows)

    assert cycle_rows[0]["tenant_id"] == "sandbox"
    assert cycle_rows[0]["number"] == 1
    assert cycle_rows[0]["cycle_time_hours"] == 24.0
    assert cycle_rows[0]["cycle_time_days"] == 1.0
    assert cycle_rows[1]["number"] == 2
    assert cycle_rows[1]["merged"] is False
    assert cycle_rows[1]["cycle_time_hours"] is None
    assert cycle_rows[1]["cycle_time_days"] is None


def test_materialize_tenant_github_gold_writes_delta_metric_tables(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    write_silver_pull_requests(
        "sandbox",
        [
            silver_pull_request_row(number=1),
            silver_pull_request_row(
                number=2,
                created_at=datetime(2026, 6, 3, 9, 0, tzinfo=UTC),
                closed_at=None,
                merged_at=None,
                merged=False,
            ),
        ],
    )

    result = materialize_tenant_github_gold("sandbox")

    assert result.tenant_id == "sandbox"
    assert [(write.table_name, write.row_count) for write in result.writes] == [
        (PR_THROUGHPUT_DAILY_TABLE, 3),
        (PR_CYCLE_TIME_TABLE, 2),
    ]

    throughput_path = delta_table_path("sandbox", "gold", "github", PR_THROUGHPUT_DAILY_TABLE)
    cycle_time_path = delta_table_path("sandbox", "gold", "github", PR_CYCLE_TIME_TABLE)
    throughput_rows = DeltaTable(str(throughput_path)).to_pyarrow_table().to_pylist()
    cycle_time_rows = DeltaTable(str(cycle_time_path)).to_pyarrow_table().to_pylist()

    assert throughput_rows[0]["tenant_id"] == "sandbox"
    assert sum(row["opened_count"] for row in throughput_rows) == 2
    assert sum(row["merged_count"] for row in throughput_rows) == 1
    assert cycle_time_rows[0]["tenant_id"] == "sandbox"
    assert cycle_time_rows[0]["cycle_time_hours"] == 24.0
    assert cycle_time_rows[1]["cycle_time_hours"] is None
    assert (throughput_path / "_delta_log").exists()
    assert (cycle_time_path / "_delta_log").exists()


def test_gold_metrics_keep_tenant_paths_separate(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    write_silver_pull_requests("sandbox", [silver_pull_request_row(tenant_id="sandbox")])
    write_silver_pull_requests(
        "personal",
        [
            silver_pull_request_row(
                tenant_id="personal",
                repository_full_name="crlough/kabuto-kurage",
                number=7,
            )
        ],
    )

    materialize_tenant_github_gold("sandbox")
    materialize_tenant_github_gold("personal")

    sandbox_rows = DeltaTable(
        str(delta_table_path("sandbox", "gold", "github", PR_CYCLE_TIME_TABLE))
    ).to_pyarrow_table().to_pylist()
    personal_rows = DeltaTable(
        str(delta_table_path("personal", "gold", "github", PR_CYCLE_TIME_TABLE))
    ).to_pyarrow_table().to_pylist()

    assert sandbox_rows == [
        {**sandbox_rows[0], "tenant_id": "sandbox", "repository_full_name": "octocat/Hello-World"}
    ]
    assert personal_rows == [
        {
            **personal_rows[0],
            "tenant_id": "personal",
            "repository_full_name": "crlough/kabuto-kurage",
        }
    ]


def test_gold_metric_schemas_are_explicit_about_tables() -> None:
    assert "opened_count" in PR_THROUGHPUT_DAILY_SCHEMA.names
    assert "cycle_time_hours" in PR_CYCLE_TIME_SCHEMA.names
