from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from kabuto_kurage.ingestion.github_bronze import (
    REPOSITORY_RESOURCE,
    RateLimitSnapshot,
    repository_payload_to_bronze_record,
    write_bronze_records,
)
from kabuto_kurage.observability import (
    GITHUB_TABLE_CONFIGS,
    collect_github_observability,
    observe_github_table,
)
from kabuto_kurage.observability import (
    main as observability_main,
)
from kabuto_kurage.paths import delta_table_path

FETCHED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
NOW = datetime(2026, 6, 18, 13, 0, tzinfo=UTC)


def repository_payload() -> dict[str, object]:
    return {
        "id": 1296269,
        "node_id": "repo-node-1",
        "name": "Hello-World",
        "full_name": "octocat/Hello-World",
        "owner": {"login": "octocat"},
        "html_url": "https://github.com/octocat/Hello-World",
        "url": "https://api.github.com/repos/octocat/Hello-World",
    }


def repository_config():
    return next(
        config
        for config in GITHUB_TABLE_CONFIGS
        if config.layer == "bronze" and config.resource_type == REPOSITORY_RESOURCE
    )


def test_observability_reports_missing_and_empty_tables(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    config = repository_config()

    missing = observe_github_table(tenant_id="sandbox", config=config, now=NOW)
    assert missing.table_exists is False
    assert missing.row_count == 0
    assert missing.freshness_status == "missing"

    empty_path = delta_table_path("sandbox", "bronze", "github", "repositories")
    write_bronze_records(empty_path, [])
    empty = observe_github_table(tenant_id="sandbox", config=config, now=NOW)
    assert empty.table_exists is True
    assert empty.row_count == 0
    assert empty.delta_version == 0
    assert empty.freshness_status == "empty"
    assert empty.latest_successful_ingestion_at is None


def test_observability_reports_freshness_row_count_and_rate_limits(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    table_path = delta_table_path("sandbox", "bronze", "github", "repositories")
    write_bronze_records(
        table_path,
        [
            repository_payload_to_bronze_record(
                tenant_id="sandbox",
                payload=repository_payload(),
                fetched_at=FETCHED_AT,
                ingestion_run_id="run-123",
                rate_limit=RateLimitSnapshot(
                    limit=5000,
                    remaining=4998,
                    used=2,
                    reset_epoch_seconds=1781800000,
                    resource="core",
                ),
            )
        ],
    )

    observed = observe_github_table(
        tenant_id="sandbox",
        config=repository_config(),
        now=NOW,
        stale_after_hours=2,
    )

    assert observed.table_exists is True
    assert observed.row_count == 1
    assert observed.latest_successful_ingestion_at == FETCHED_AT
    assert observed.latest_ingestion_run_id == "run-123"
    assert observed.freshness_status == "fresh"
    assert observed.freshness_lag_seconds == 3600.0
    assert observed.rate_limit_limit == 5000
    assert observed.rate_limit_remaining_min == 4998
    assert observed.rate_limit_used_max == 2
    assert observed.as_dagster_metadata()["freshness_lag_hours"] == 1.0

    stale = observe_github_table(
        tenant_id="sandbox",
        config=repository_config(),
        now=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
        stale_after_hours=24,
    )
    assert stale.freshness_status == "stale"


def test_collect_github_observability_reports_all_known_tables(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))

    records = collect_github_observability(tenant_ids=("sandbox",), now=NOW)

    assert len(records) == 6
    assert {record.tenant_id for record in records} == {"sandbox"}
    assert {record.source for record in records} == {"github"}
    assert {record.freshness_status for record in records} == {"missing"}


def test_observability_cli_outputs_last_ingested_state(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    write_bronze_records(
        delta_table_path("sandbox", "bronze", "github", "repositories"),
        [
            repository_payload_to_bronze_record(
                tenant_id="sandbox",
                payload=repository_payload(),
                fetched_at=FETCHED_AT,
                ingestion_run_id="run-cli",
                rate_limit=RateLimitSnapshot(5000, 4000, 1000, 1781800000, "core"),
            )
        ],
    )

    observability_main(["--tenant", "sandbox", "--format", "json"])
    output = json.loads(capsys.readouterr().out)

    assert output["data_root"] == str(tmp_path)
    repository_record = next(
        record
        for record in output["records"]
        if record["layer"] == "bronze" and record["resource_type"] == "repositories"
    )
    assert repository_record["row_count"] == 1
    assert repository_record["latest_ingestion_run_id"] == "run-cli"
    assert repository_record["rate_limit_remaining_min"] == 4000
