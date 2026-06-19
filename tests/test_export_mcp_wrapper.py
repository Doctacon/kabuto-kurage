from __future__ import annotations

import asyncio
import json
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest
from deltalake import write_deltalake

from kabuto_kurage.api.auth import APIAuthError, TenantAccessDeniedError
from kabuto_kurage.mcp_server import (
    MCP_TOOL_NAMES,
    create_mcp_server,
    github_metrics_summary,
    github_pr_cycle_time,
    github_pr_throughput_daily,
)
from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.transforms.github_gold import (
    PR_CYCLE_TIME_SCHEMA,
    PR_CYCLE_TIME_TABLE,
    PR_THROUGHPUT_DAILY_SCHEMA,
    PR_THROUGHPUT_DAILY_TABLE,
)

FETCHED_AT = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)


@pytest.fixture
def seeded_mcp_gold_tables(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv(
        "KABUTO_API_TOKENS_JSON",
        json.dumps(
            {
                "sandbox-mcp-token": ["sandbox"],
                "personal-mcp-token": ["personal"],
            }
        ),
    )
    write_gold_rows(
        "sandbox",
        table_name=PR_THROUGHPUT_DAILY_TABLE,
        schema=PR_THROUGHPUT_DAILY_SCHEMA,
        rows=[
            throughput_row(metric_date=date(2026, 6, 1), opened_count=2),
            throughput_row(metric_date=date(2026, 6, 2), merged_count=1, closed_count=1),
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
    return tmp_path


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


def assert_no_raw_or_secret_fields(payload: object) -> None:
    encoded = json.dumps(payload)
    assert "payload_json" not in encoded
    assert "source" not in encoded
    assert "sandbox-mcp-token" not in encoded
    assert "personal-mcp-token" not in encoded
    assert "token" not in encoded.lower()


def test_mcp_server_exposes_only_initial_three_metric_tools() -> None:
    async def list_tool_names() -> list[str]:
        tools = await create_mcp_server().list_tools()
        return sorted(tool.name for tool in tools)

    assert asyncio.run(list_tool_names()) == sorted(MCP_TOOL_NAMES)


def test_mcp_tool_schemas_require_explicit_tenant_id_and_token() -> None:
    async def list_tools() -> dict[str, Any]:
        return {tool.name: tool.inputSchema for tool in await create_mcp_server().list_tools()}

    schemas = asyncio.run(list_tools())
    for tool_name, schema in schemas.items():
        assert tool_name in MCP_TOOL_NAMES
        assert set(schema["required"]) >= {"tenant_id", "api_token"}


def test_mcp_tools_return_query_contract_json_for_allowed_tenant(
    seeded_mcp_gold_tables: Path,
) -> None:
    throughput = github_pr_throughput_daily(
        tenant_id="sandbox",
        api_token="sandbox-mcp-token",
        start_date="2026-06-01",
        end_date="2026-06-02",
        repository_full_name="octocat/Hello-World",
        limit=1,
        offset=1,
    )
    cycle_time = github_pr_cycle_time(
        tenant_id="sandbox",
        api_token="sandbox-mcp-token",
        start_date="2026-06-01",
        end_date="2026-06-03",
        repository_full_name=["octocat/Hello-World"],
        merged=True,
        limit=2,
    )
    summary = github_metrics_summary(
        tenant_id="sandbox",
        api_token="sandbox-mcp-token",
        start_date="2026-06-01",
        end_date="2026-06-03",
        repository_full_name="octocat/Hello-World",
    )

    assert throughput == [
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
    assert [record["number"] for record in cycle_time] == [1, 2]
    assert {record["tenant_id"] for record in cycle_time} == {"sandbox"}
    assert summary == {
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
    assert_no_raw_or_secret_fields(throughput)
    assert_no_raw_or_secret_fields(cycle_time)
    assert_no_raw_or_secret_fields(summary)


def test_mcp_tools_reject_missing_and_invalid_tokens(seeded_mcp_gold_tables: Path) -> None:
    with pytest.raises(APIAuthError, match="Missing Authorization bearer token"):
        github_metrics_summary(tenant_id="sandbox", api_token="")

    with pytest.raises(APIAuthError, match="Invalid bearer token"):
        github_metrics_summary(tenant_id="sandbox", api_token="not-a-valid-token")


def test_mcp_tools_reject_disallowed_tenant_and_do_not_leak_cross_tenant_data(
    seeded_mcp_gold_tables: Path,
) -> None:
    with pytest.raises(TenantAccessDeniedError, match="not allowed to access tenant personal"):
        github_pr_cycle_time(tenant_id="personal", api_token="sandbox-mcp-token")

    records = github_pr_cycle_time(tenant_id="sandbox", api_token="sandbox-mcp-token")
    assert {record["tenant_id"] for record in records} == {"sandbox"}
    assert "crlough/kabuto-kurage" not in {record["repository_full_name"] for record in records}
    assert_no_raw_or_secret_fields(records)
