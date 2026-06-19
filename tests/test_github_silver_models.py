from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deltalake import DeltaTable

from kabuto_kurage.ingestion.github_bronze import (
    pull_request_payload_to_bronze_record,
    repository_payload_to_bronze_record,
    write_bronze_records,
)
from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.transforms.github_silver import (
    materialize_tenant_github_silver,
    transform_pull_request_bronze_rows,
    transform_repository_bronze_rows,
)

FETCHED_AT = datetime(2026, 6, 18, 12, 0, 0, tzinfo=UTC)


def repository_payload(full_name: str = "octocat/Hello-World") -> dict[str, Any]:
    owner, name = full_name.split("/", 1)
    return {
        "id": 1296269,
        "node_id": "MDEwOlJlcG9zaXRvcnkxMjk2MjY5",
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
        "description": "Fixture repository",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "pushed_at": "2026-06-02T00:00:00Z",
        "unexpected_future_field": {"kept_in_bronze_only": True},
    }


def pull_request_payload(full_name: str = "octocat/Hello-World") -> dict[str, Any]:
    return {
        "id": 1,
        "node_id": "MDExOlB1bGxSZXF1ZXN0MQ==",
        "number": 1347,
        "state": "closed",
        "title": "Improve README",
        "user": {"login": "octocat"},
        "author_association": "OWNER",
        "draft": False,
        "html_url": f"https://github.com/{full_name}/pull/1347",
        "url": f"https://api.github.com/repos/{full_name}/pulls/1347",
        "base": {"ref": "main", "repo": {"full_name": full_name}},
        "head": {"ref": "feature/readme", "repo": {"full_name": "contributor/fork"}},
        "created_at": "2026-06-01T00:00:00Z",
        "updated_at": "2026-06-01T12:00:00Z",
        "closed_at": "2026-06-02T00:00:00Z",
        "merged_at": "2026-06-02T00:00:00Z",
        "future_nested_payload": {"kept_in_bronze_only": True},
    }


def bronze_repository_record(
    tenant_id: str = "sandbox", payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    return repository_payload_to_bronze_record(
        tenant_id=tenant_id,
        payload=payload or repository_payload(),
        fetched_at=FETCHED_AT,
        ingestion_run_id="run-123",
        rate_limit=None,
    )


def bronze_pull_request_record(
    tenant_id: str = "sandbox", payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    return pull_request_payload_to_bronze_record(
        tenant_id=tenant_id,
        payload=payload or pull_request_payload(),
        fetched_at=FETCHED_AT,
        ingestion_run_id="run-123",
        rate_limit=None,
    )


def test_repository_silver_transform_extracts_typed_stable_columns() -> None:
    [record] = transform_repository_bronze_rows([bronze_repository_record()])

    assert record["tenant_id"] == "sandbox"
    assert record["source"] == "github"
    assert record["repository_id"] == 1296269
    assert record["repository_node_id"] == "MDEwOlJlcG9zaXRvcnkxMjk2MjY5"
    assert record["owner_login"] == "octocat"
    assert record["full_name"] == "octocat/Hello-World"
    assert record["private"] is False
    assert record["fork"] is False
    assert record["archived"] is False
    assert record["disabled"] is False
    assert record["default_branch"] == "main"
    assert record["language"] == "Python"
    assert record["created_at"] == datetime(2026, 1, 1, tzinfo=UTC)
    assert record["fetched_at"] == FETCHED_AT
    assert record["ingestion_run_id"] == "run-123"
    assert record["bronze_source_id"] == "MDEwOlJlcG9zaXRvcnkxMjk2MjY5"
    assert record["bronze_source_url"] == "https://github.com/octocat/Hello-World"


def test_pull_request_silver_transform_extracts_typed_stable_columns() -> None:
    [record] = transform_pull_request_bronze_rows([bronze_pull_request_record()])

    assert record["tenant_id"] == "sandbox"
    assert record["source"] == "github"
    assert record["pull_request_id"] == 1
    assert record["pull_request_node_id"] == "MDExOlB1bGxSZXF1ZXN0MQ=="
    assert record["repository_full_name"] == "octocat/Hello-World"
    assert record["repository_owner"] == "octocat"
    assert record["number"] == 1347
    assert record["state"] == "closed"
    assert record["user_login"] == "octocat"
    assert record["draft"] is False
    assert record["merged"] is True
    assert record["created_at"] == datetime(2026, 6, 1, tzinfo=UTC)
    assert record["merged_at"] == datetime(2026, 6, 2, tzinfo=UTC)
    assert record["base_ref"] == "main"
    assert record["head_ref"] == "feature/readme"
    assert record["base_repo_full_name"] == "octocat/Hello-World"
    assert record["head_repo_full_name"] == "contributor/fork"
    assert record["bronze_api_url"] == "https://api.github.com/repos/octocat/Hello-World/pulls/1347"


def test_silver_transforms_handle_missing_and_null_payload_fields_gracefully() -> None:
    sparse_repository = {
        "id": "42",
        "node_id": "repo-node",
        "full_name": "octocat/sparse-repo",
        "private": None,
        "created_at": "not-a-timestamp",
    }
    sparse_pull_request = {
        "id": "99",
        "node_id": "pr-node",
        "number": "7",
        "state": "open",
        "base": {"repo": None},
        "head": None,
        "merged_at": None,
    }

    [repository] = transform_repository_bronze_rows(
        [bronze_repository_record(payload=sparse_repository)]
    )
    [pull_request] = transform_pull_request_bronze_rows(
        [bronze_pull_request_record(payload=sparse_pull_request)]
    )

    assert repository["repository_id"] == 42
    assert repository["owner_login"] is None
    assert repository["name"] is None
    assert repository["private"] is None
    assert repository["created_at"] is None
    assert repository["full_name"] == "octocat/sparse-repo"

    assert pull_request["pull_request_id"] == 99
    assert pull_request["number"] == 7
    assert pull_request["repository_full_name"] is None
    assert pull_request["repository_owner"] is None
    assert pull_request["user_login"] is None
    assert pull_request["draft"] is None
    assert pull_request["merged"] is False
    assert pull_request["base_ref"] is None
    assert pull_request["head_repo_full_name"] is None


def test_materialize_tenant_github_silver_writes_delta_tables(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    bronze_repositories_path = delta_table_path("sandbox", "bronze", "github", "repositories")
    bronze_pull_requests_path = delta_table_path("sandbox", "bronze", "github", "pull_requests")
    write_bronze_records(bronze_repositories_path, [bronze_repository_record()])
    write_bronze_records(bronze_pull_requests_path, [bronze_pull_request_record()])

    result = materialize_tenant_github_silver("sandbox")

    assert result.tenant_id == "sandbox"
    assert [(write.table_name, write.row_count) for write in result.writes] == [
        ("repositories", 1),
        ("pull_requests", 1),
    ]

    silver_repositories_path = delta_table_path("sandbox", "silver", "github", "repositories")
    silver_pull_requests_path = delta_table_path("sandbox", "silver", "github", "pull_requests")
    repository_rows = DeltaTable(str(silver_repositories_path)).to_pyarrow_table().to_pylist()
    pull_request_rows = DeltaTable(str(silver_pull_requests_path)).to_pyarrow_table().to_pylist()

    assert repository_rows[0]["tenant_id"] == "sandbox"
    assert repository_rows[0]["full_name"] == "octocat/Hello-World"
    assert repository_rows[0]["repository_id"] == 1296269
    assert pull_request_rows[0]["tenant_id"] == "sandbox"
    assert pull_request_rows[0]["repository_full_name"] == "octocat/Hello-World"
    assert pull_request_rows[0]["number"] == 1347
    assert (silver_repositories_path / "_delta_log").exists()
    assert (silver_pull_requests_path / "_delta_log").exists()


def test_materialize_tenant_github_silver_keeps_tenant_paths_separate(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    for tenant_id, full_name in [
        ("sandbox", "octocat/Hello-World"),
        ("personal", "crlough/kabuto-kurage"),
    ]:
        write_bronze_records(
            delta_table_path(tenant_id, "bronze", "github", "repositories"),
            [bronze_repository_record(tenant_id, repository_payload(full_name))],
        )
        write_bronze_records(
            delta_table_path(tenant_id, "bronze", "github", "pull_requests"),
            [bronze_pull_request_record(tenant_id, pull_request_payload(full_name))],
        )
        materialize_tenant_github_silver(tenant_id)

    sandbox_rows = DeltaTable(
        str(delta_table_path("sandbox", "silver", "github", "repositories"))
    ).to_pyarrow_table().to_pylist()
    personal_rows = DeltaTable(
        str(delta_table_path("personal", "silver", "github", "repositories"))
    ).to_pyarrow_table().to_pylist()

    assert sandbox_rows == [
        {**sandbox_rows[0], "tenant_id": "sandbox", "full_name": "octocat/Hello-World"}
    ]
    assert personal_rows == [
        {**personal_rows[0], "tenant_id": "personal", "full_name": "crlough/kabuto-kurage"}
    ]
