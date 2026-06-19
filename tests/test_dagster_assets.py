from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dagster import materialize
from deltalake import DeltaTable

import kabuto_kurage.assets.github as github_assets
from kabuto_kurage.definitions import defs
from kabuto_kurage.ingestion.github_bronze import (
    BronzeWriteResult,
    GitHubBronzeIngestionResult,
    RateLimitSnapshot,
    pull_request_payload_to_bronze_record,
    repository_payload_to_bronze_record,
    write_bronze_records,
)
from kabuto_kurage.paths import delta_table_path

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
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-06-01T00:00:00Z",
        "pushed_at": "2026-06-02T00:00:00Z",
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
    }


def test_definitions_expose_partitioned_github_assets_through_gold_metrics() -> None:
    specs = {spec.key.to_user_string(): spec for spec in defs.resolve_all_asset_specs()}

    assert set(specs) >= {
        "github_bronze_repositories",
        "github_bronze_pull_requests",
        "github_silver_repositories",
        "github_silver_pull_requests",
        "github_gold_pr_throughput_daily",
        "github_gold_pr_cycle_time",
    }
    assert specs["github_bronze_repositories"].group_name == "github_bronze"
    assert specs["github_silver_pull_requests"].group_name == "github_silver"
    assert specs["github_gold_pr_cycle_time"].group_name == "github_gold"
    assert [dep.asset_key.to_user_string() for dep in specs["github_gold_pr_cycle_time"].deps] == [
        "github_silver_pull_requests"
    ]
    assert specs["github_bronze_repositories"].partitions_def is not None
    assert specs["github_bronze_repositories"].partitions_def.get_partition_keys() == (
        "personal",
        "sandbox",
    )


def test_github_asset_graph_materializes_bronze_silver_and_gold_without_live_github(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("KABUTO_GITHUB_MAX_REPOSITORIES", "1")

    def fake_ingest_tenant_github_to_bronze(
        tenant: Any,
        *,
        token: str | None = None,
        ingestion_run_id: str | None = None,
        fetched_at: datetime | None = None,
        client: object | None = None,
        max_repositories: int | None = None,
    ) -> GitHubBronzeIngestionResult:
        del token, client
        tenant_id = tenant.tenant_id
        assert tenant_id == "sandbox"
        assert max_repositories == 1
        run_id = ingestion_run_id or "dagster-test-run"
        run_fetched_at = fetched_at or FETCHED_AT
        repository_path = delta_table_path(tenant_id, "bronze", "github", "repositories")
        pull_request_path = delta_table_path(tenant_id, "bronze", "github", "pull_requests")
        write_bronze_records(
            repository_path,
            [
                repository_payload_to_bronze_record(
                    tenant_id=tenant_id,
                    payload=repository_payload(),
                    fetched_at=run_fetched_at,
                    ingestion_run_id=run_id,
                    rate_limit=RateLimitSnapshot(5000, 4999, 1, 1781800000, "core"),
                )
            ],
        )
        write_bronze_records(
            pull_request_path,
            [
                pull_request_payload_to_bronze_record(
                    tenant_id=tenant_id,
                    payload=pull_request_payload(),
                    fetched_at=run_fetched_at,
                    ingestion_run_id=run_id,
                    rate_limit=RateLimitSnapshot(5000, 4998, 2, 1781800000, "core"),
                )
            ],
        )
        return GitHubBronzeIngestionResult(
            tenant_id=tenant_id,
            ingestion_run_id=run_id,
            fetched_at=run_fetched_at,
            repository_count=1,
            pull_request_count=1,
            writes=(
                BronzeWriteResult("repositories", repository_path, 1),
                BronzeWriteResult("pull_requests", pull_request_path, 1),
            ),
            rate_limits=(
                RateLimitSnapshot(5000, 4999, 1, 1781800000, "core"),
                RateLimitSnapshot(5000, 4998, 2, 1781800000, "core"),
            ),
        )

    monkeypatch.setattr(
        github_assets,
        "ingest_tenant_github_to_bronze",
        fake_ingest_tenant_github_to_bronze,
    )

    result = materialize(
        [
            github_assets.github_bronze_assets,
            github_assets.github_silver_assets,
            github_assets.github_gold_assets,
        ],
        partition_key="sandbox",
        raise_on_error=True,
    )

    assert result.success
    materializations = {}
    for event in result.get_asset_materialization_events():
        materialization = event.event_specific_data.materialization
        materializations[materialization.asset_key.to_user_string()] = materialization
    assert set(materializations) == {
        "github_bronze_repositories",
        "github_bronze_pull_requests",
        "github_silver_repositories",
        "github_silver_pull_requests",
        "github_gold_pr_throughput_daily",
        "github_gold_pr_cycle_time",
    }
    for name, materialization in materializations.items():
        expected_count = 2 if name == "github_gold_pr_throughput_daily" else 1
        assert materialization.metadata["row_count"].value == expected_count
        assert materialization.metadata["tenant_id"].value == "sandbox"
        assert materialization.metadata["source"].value == "github"
        assert "delta_table_path" in materialization.metadata
        assert materialization.metadata["delta_version"].value == 0

    assert materializations["github_bronze_pull_requests"].metadata[
        "minimum_rate_limit_remaining"
    ].value == 4998
    assert materializations["github_silver_pull_requests"].metadata[
        "latest_ingestion_run_id"
    ].value == "dagster-test-run"

    assert materializations["github_gold_pr_throughput_daily"].metadata[
        "metric_grain"
    ].value == "tenant_repository_day"
    assert materializations["github_gold_pr_cycle_time"].metadata["duration_unit"].value == (
        "hours_and_days"
    )

    silver_pr_rows = DeltaTable(
        str(delta_table_path("sandbox", "silver", "github", "pull_requests"))
    ).to_pyarrow_table().to_pylist()
    gold_cycle_rows = DeltaTable(
        str(delta_table_path("sandbox", "gold", "github", "pr_cycle_time"))
    ).to_pyarrow_table().to_pylist()
    assert silver_pr_rows == [
        {**silver_pr_rows[0], "tenant_id": "sandbox", "repository_full_name": "octocat/Hello-World"}
    ]
    assert gold_cycle_rows == [
        {
            **gold_cycle_rows[0],
            "tenant_id": "sandbox",
            "repository_full_name": "octocat/Hello-World",
            "cycle_time_hours": 24.0,
        }
    ]
