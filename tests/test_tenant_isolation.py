from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest
from deltalake import DeltaTable, write_deltalake

from kabuto_kurage.ingestion.github_bronze import (
    pull_request_payload_to_bronze_record,
    repository_payload_to_bronze_record,
    write_bronze_records,
)
from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.transforms.github_gold import (
    PR_CYCLE_TIME_TABLE,
    PR_THROUGHPUT_DAILY_TABLE,
    GitHubGoldMetricError,
    materialize_tenant_github_gold,
)
from kabuto_kurage.transforms.github_silver import (
    PULL_REQUESTS_SILVER_SCHEMA,
    GitHubSilverTransformError,
    materialize_tenant_github_silver,
)

FETCHED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


def repository_payload(full_name: str, repository_id: int) -> dict[str, Any]:
    owner, name = full_name.split("/", 1)
    return {
        "id": repository_id,
        "node_id": f"repo-node-{repository_id}",
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


def pull_request_payload(
    full_name: str,
    *,
    number: int,
    pull_request_id: int,
    created_at: str,
    closed_at: str | None,
    merged_at: str | None,
) -> dict[str, Any]:
    return {
        "id": pull_request_id,
        "node_id": f"pr-node-{pull_request_id}",
        "number": number,
        "state": "closed" if closed_at else "open",
        "title": f"PR {number}",
        "user": {"login": "octocat"},
        "author_association": "OWNER",
        "draft": False,
        "html_url": f"https://github.com/{full_name}/pull/{number}",
        "url": f"https://api.github.com/repos/{full_name}/pulls/{number}",
        "base": {"ref": "main", "repo": {"full_name": full_name}},
        "head": {"ref": f"feature/{number}", "repo": {"full_name": full_name}},
        "created_at": created_at,
        "updated_at": created_at,
        "closed_at": closed_at,
        "merged_at": merged_at,
    }


def seed_bronze_tenant(
    tenant_id: str,
    *,
    full_name: str,
    repository_id: int,
    pull_requests: list[dict[str, Any]],
) -> None:
    repository_path = delta_table_path(tenant_id, "bronze", "github", "repositories")
    pull_requests_path = delta_table_path(tenant_id, "bronze", "github", "pull_requests")
    write_bronze_records(
        repository_path,
        [
            repository_payload_to_bronze_record(
                tenant_id=tenant_id,
                payload=repository_payload(full_name, repository_id),
                fetched_at=FETCHED_AT,
                ingestion_run_id=f"run-{tenant_id}",
                rate_limit=None,
            )
        ],
    )
    write_bronze_records(
        pull_requests_path,
        [
            pull_request_payload_to_bronze_record(
                tenant_id=tenant_id,
                payload=pull_request,
                fetched_at=FETCHED_AT,
                ingestion_run_id=f"run-{tenant_id}",
                rate_limit=None,
            )
            for pull_request in pull_requests
        ],
    )


def read_delta_rows(tenant_id: str, layer: str, table_name: str) -> list[dict[str, Any]]:
    table_path = delta_table_path(tenant_id, layer, "github", table_name)
    rows = DeltaTable(str(table_path)).to_pyarrow_table().to_pylist()
    return [dict(row) for row in rows]


def assert_only_tenant(rows: list[dict[str, Any]], tenant_id: str) -> None:
    assert rows, f"Expected rows for {tenant_id}"
    assert {row["tenant_id"] for row in rows} == {tenant_id}


def test_bronze_silver_gold_layers_keep_two_tenants_isolated(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    seed_bronze_tenant(
        "sandbox",
        full_name="octocat/Hello-World",
        repository_id=1,
        pull_requests=[
            pull_request_payload(
                "octocat/Hello-World",
                number=1,
                pull_request_id=101,
                created_at="2026-06-01T10:00:00Z",
                closed_at="2026-06-02T10:00:00Z",
                merged_at="2026-06-02T10:00:00Z",
            ),
            pull_request_payload(
                "octocat/Hello-World",
                number=2,
                pull_request_id=102,
                created_at="2026-06-03T10:00:00Z",
                closed_at=None,
                merged_at=None,
            ),
        ],
    )
    seed_bronze_tenant(
        "personal",
        full_name="crlough/kabuto-kurage",
        repository_id=2,
        pull_requests=[
            pull_request_payload(
                "crlough/kabuto-kurage",
                number=7,
                pull_request_id=207,
                created_at="2026-07-01T10:00:00Z",
                closed_at="2026-07-04T10:00:00Z",
                merged_at="2026-07-04T10:00:00Z",
            )
        ],
    )

    for tenant_id in ("sandbox", "personal"):
        materialize_tenant_github_silver(tenant_id)
        materialize_tenant_github_gold(tenant_id)

    for tenant_id in ("sandbox", "personal"):
        assert_only_tenant(read_delta_rows(tenant_id, "bronze", "repositories"), tenant_id)
        assert_only_tenant(read_delta_rows(tenant_id, "bronze", "pull_requests"), tenant_id)
        assert_only_tenant(read_delta_rows(tenant_id, "silver", "repositories"), tenant_id)
        assert_only_tenant(read_delta_rows(tenant_id, "silver", "pull_requests"), tenant_id)
        assert_only_tenant(read_delta_rows(tenant_id, "gold", PR_THROUGHPUT_DAILY_TABLE), tenant_id)
        assert_only_tenant(read_delta_rows(tenant_id, "gold", PR_CYCLE_TIME_TABLE), tenant_id)

    sandbox_cycle_rows = read_delta_rows("sandbox", "gold", PR_CYCLE_TIME_TABLE)
    personal_cycle_rows = read_delta_rows("personal", "gold", PR_CYCLE_TIME_TABLE)
    assert {row["repository_full_name"] for row in sandbox_cycle_rows} == {"octocat/Hello-World"}
    assert {row["number"] for row in sandbox_cycle_rows} == {1, 2}
    assert {row["repository_full_name"] for row in personal_cycle_rows} == {
        "crlough/kabuto-kurage"
    }
    assert {row["number"] for row in personal_cycle_rows} == {7}

    sandbox_throughput_rows = read_delta_rows("sandbox", "gold", PR_THROUGHPUT_DAILY_TABLE)
    personal_throughput_rows = read_delta_rows("personal", "gold", PR_THROUGHPUT_DAILY_TABLE)
    assert {row["repository_full_name"] for row in sandbox_throughput_rows} == {
        "octocat/Hello-World"
    }
    assert {row["repository_full_name"] for row in personal_throughput_rows} == {
        "crlough/kabuto-kurage"
    }
    assert sum(row["opened_count"] for row in sandbox_throughput_rows) == 2
    assert sum(row["opened_count"] for row in personal_throughput_rows) == 1


def test_silver_materialization_rejects_mismatched_tenant_rows_in_bronze_path(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    write_bronze_records(
        delta_table_path("sandbox", "bronze", "github", "repositories"),
        [
            repository_payload_to_bronze_record(
                tenant_id="personal",
                payload=repository_payload("crlough/kabuto-kurage", 2),
                fetched_at=FETCHED_AT,
                ingestion_run_id="bad-run",
                rate_limit=None,
            )
        ],
    )
    write_bronze_records(
        delta_table_path("sandbox", "bronze", "github", "pull_requests"),
        [
            pull_request_payload_to_bronze_record(
                tenant_id="sandbox",
                payload=pull_request_payload(
                    "octocat/Hello-World",
                    number=1,
                    pull_request_id=101,
                    created_at="2026-06-01T10:00:00Z",
                    closed_at="2026-06-02T10:00:00Z",
                    merged_at="2026-06-02T10:00:00Z",
                ),
                fetched_at=FETCHED_AT,
                ingestion_run_id="good-run",
                rate_limit=None,
            )
        ],
    )

    with pytest.raises(GitHubSilverTransformError, match="found rows for tenant_id"):
        materialize_tenant_github_silver("sandbox")


def test_gold_materialization_rejects_mismatched_tenant_rows_in_silver_path(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    silver_path = delta_table_path("sandbox", "silver", "github", "pull_requests")
    silver_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "tenant_id": "personal",
        "source": "github",
        "pull_request_id": 207,
        "pull_request_node_id": "pr-node-207",
        "repository_full_name": "crlough/kabuto-kurage",
        "repository_owner": "crlough",
        "number": 7,
        "state": "closed",
        "title": "Wrong tenant row",
        "user_login": "octocat",
        "author_association": "OWNER",
        "draft": False,
        "merged": True,
        "created_at": datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
        "updated_at": datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
        "closed_at": datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
        "merged_at": datetime(2026, 7, 4, 10, 0, tzinfo=UTC),
        "html_url": "https://github.com/crlough/kabuto-kurage/pull/7",
        "api_url": "https://api.github.com/repos/crlough/kabuto-kurage/pulls/7",
        "base_ref": "main",
        "head_ref": "feature/7",
        "base_repo_full_name": "crlough/kabuto-kurage",
        "head_repo_full_name": "crlough/kabuto-kurage",
        "fetched_at": FETCHED_AT,
        "ingestion_run_id": "bad-run",
        "bronze_source_id": "pr-node-207",
        "bronze_source_url": "https://github.com/crlough/kabuto-kurage/pull/7",
        "bronze_api_url": "https://api.github.com/repos/crlough/kabuto-kurage/pulls/7",
    }
    columns = {field.name: [row.get(field.name)] for field in PULL_REQUESTS_SILVER_SCHEMA}
    write_deltalake(
        str(silver_path),
        pa.table(columns, schema=PULL_REQUESTS_SILVER_SCHEMA),
        mode="overwrite",
    )

    with pytest.raises(GitHubGoldMetricError, match="found rows for tenant_id"):
        materialize_tenant_github_gold("sandbox")
