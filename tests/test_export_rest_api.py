from __future__ import annotations

import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest
from deltalake import write_deltalake
from fastapi.testclient import TestClient

from kabuto_kurage.api.app import create_app
from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.transforms.github_gold import (
    PR_CYCLE_TIME_SCHEMA,
    PR_CYCLE_TIME_TABLE,
    PR_THROUGHPUT_DAILY_SCHEMA,
    PR_THROUGHPUT_DAILY_TABLE,
)

FETCHED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv(
        "KABUTO_API_TOKENS_JSON",
        json.dumps(
            {
                "sandbox-reader-token": ["sandbox"],
                "personal-reader-token": ["personal"],
                "multi-tenant-reader-token": ["sandbox", "personal"],
            }
        ),
    )
    seed_gold_tables()
    return TestClient(create_app())


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
    return {
        "tenant_id": tenant_id,
        "source": "github",
        "repository_full_name": repository_full_name,
        "repository_owner": repository_full_name.split("/", 1)[0],
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


def seed_gold_tables() -> None:
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
                opened_count=5,
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


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_no_raw_or_secret_fields(payload: object) -> None:
    encoded = json.dumps(payload)
    assert "payload_json" not in encoded
    assert "ghp_secret_should_not_appear" not in encoded
    if isinstance(payload, list):
        for record in payload:
            assert isinstance(record, dict)
            assert "source" not in record
            assert all("token" not in key.lower() for key in record)


def test_api_app_can_be_imported_and_health_checked(api_client: TestClient) -> None:
    response = api_client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_pr_throughput_endpoint_returns_query_layer_json(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/tenants/sandbox/metrics/github/pr-throughput-daily",
        params={
            "start_date": "2026-06-01",
            "end_date": "2026-06-02",
            "repository_full_name": "octocat/Hello-World",
            "limit": "1",
            "offset": "1",
        },
        headers=auth_header("sandbox-reader-token"),
    )

    assert response.status_code == 200, response.text
    assert response.json() == [
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
    assert_no_raw_or_secret_fields(response.json())


def test_pr_cycle_time_endpoint_returns_query_layer_json(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/tenants/sandbox/metrics/github/pr-cycle-time",
        params=[
            ("start_date", "2026-06-01"),
            ("end_date", "2026-06-03"),
            ("repository_full_name", "octocat/Hello-World"),
            ("merged", "true"),
            ("limit", "2"),
            ("offset", "0"),
        ],
        headers=auth_header("sandbox-reader-token"),
    )

    assert response.status_code == 200, response.text
    records = response.json()
    assert [record["number"] for record in records] == [1, 2]
    assert {record["tenant_id"] for record in records} == {"sandbox"}
    assert records[0]["created_at"] == "2026-06-01T10:00:00+00:00"
    assert_no_raw_or_secret_fields(records)


def test_summary_endpoint_returns_query_layer_json(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/tenants/sandbox/metrics/github/summary",
        params=[
            ("start_date", "2026-06-01"),
            ("end_date", "2026-06-03"),
            ("repository_full_name", "octocat/Hello-World"),
        ],
        headers=auth_header("sandbox-reader-token"),
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
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
    assert_no_raw_or_secret_fields(response.json())


def test_missing_invalid_and_disallowed_tokens_return_predictable_errors(
    api_client: TestClient,
) -> None:
    path = "/api/v1/tenants/sandbox/metrics/github/summary"

    missing = api_client.get(path)
    assert missing.status_code == 401
    assert missing.headers["www-authenticate"] == "Bearer"
    assert missing.json() == {
        "detail": {"error": "unauthorized", "message": "Missing Authorization bearer token"}
    }

    invalid = api_client.get(path, headers=auth_header("not-a-valid-token"))
    assert invalid.status_code == 401
    assert invalid.json() == {
        "detail": {"error": "unauthorized", "message": "Invalid bearer token"}
    }

    disallowed = api_client.get(path, headers=auth_header("personal-reader-token"))
    assert disallowed.status_code == 403
    assert disallowed.json() == {
        "detail": {
            "error": "forbidden",
            "message": "Token is not allowed to access tenant sandbox",
        }
    }


def test_tenant_a_token_cannot_read_tenant_b_data(api_client: TestClient) -> None:
    blocked_response = api_client.get(
        "/api/v1/tenants/personal/metrics/github/pr-cycle-time",
        headers=auth_header("sandbox-reader-token"),
    )
    assert blocked_response.status_code == 403

    allowed_response = api_client.get(
        "/api/v1/tenants/sandbox/metrics/github/pr-cycle-time",
        headers=auth_header("sandbox-reader-token"),
    )
    assert allowed_response.status_code == 200
    records = allowed_response.json()
    assert {record["tenant_id"] for record in records} == {"sandbox"}
    assert "crlough/kabuto-kurage" not in {record["repository_full_name"] for record in records}
    assert_no_raw_or_secret_fields(records)


def test_token_allowlists_can_be_loaded_from_ignored_config_env_refs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    monkeypatch.delenv("KABUTO_API_TOKENS_JSON", raising=False)
    monkeypatch.setenv("SANDBOX_EXPORT_API_TOKEN", "sandbox-config-token")
    token_config_path = tmp_path / "api-tokens.yaml"
    token_config_path.write_text(
        "tokens:\n"
        "  - token_env: SANDBOX_EXPORT_API_TOKEN\n"
        "    tenant_ids:\n"
        "      - sandbox\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KABUTO_API_TOKENS_CONFIG", str(token_config_path))
    seed_gold_tables()

    client = TestClient(create_app())
    response = client.get(
        "/api/v1/tenants/sandbox/metrics/github/summary",
        headers=auth_header("sandbox-config-token"),
    )

    assert response.status_code == 200, response.text
    assert response.json()["tenant_id"] == "sandbox"


def test_api_maps_query_validation_errors_to_predictable_json(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/v1/tenants/sandbox/metrics/github/summary",
        params={"start_date": "2026-06-03", "end_date": "2026-06-01"},
        headers=auth_header("sandbox-reader-token"),
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "error": "query_error",
            "message": "end_date must be greater than or equal to start_date",
        }
    }
