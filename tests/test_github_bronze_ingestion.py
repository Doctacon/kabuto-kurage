from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from deltalake import DeltaTable

from kabuto_kurage.ingestion.github_bronze import (
    GitHubRestClient,
    RateLimitSnapshot,
    ingest_tenant_github_to_bronze,
    pull_request_payload_to_bronze_record,
    repository_payload_to_bronze_record,
)
from kabuto_kurage.paths import delta_table_path
from kabuto_kurage.tenancy import GitHubSourceConfig, TenantConfig

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
        "unexpected_future_field": {"kept": True},
    }


def pull_request_payload(full_name: str = "octocat/Hello-World") -> dict[str, Any]:
    return {
        "id": 1,
        "node_id": "MDExOlB1bGxSZXF1ZXN0MQ==",
        "number": 1347,
        "state": "closed",
        "title": "Improve README",
        "html_url": f"https://github.com/{full_name}/pull/1347",
        "url": f"https://api.github.com/repos/{full_name}/pulls/1347",
        "base": {"repo": {"full_name": full_name}},
        "head": {"repo": {"full_name": "contributor/fork"}},
        "created_at": "2026-06-01T00:00:00Z",
        "merged_at": "2026-06-02T00:00:00Z",
    }


def tenant_config() -> TenantConfig:
    return TenantConfig(
        tenant_id="sandbox",
        display_name="Sandbox",
        github=GitHubSourceConfig(
            token_env="GITHUB_TOKEN",
            api_base_url="https://api.github.test",
            owners=("octocat",),
            repositories=("octocat/Hello-World",),
        ),
    )


def response(body: object, *, link: str | None = None, remaining: str = "4999") -> httpx.Response:
    headers = {
        "x-ratelimit-limit": "5000",
        "x-ratelimit-remaining": remaining,
        "x-ratelimit-used": str(5000 - int(remaining)),
        "x-ratelimit-reset": "1781800000",
        "x-ratelimit-resource": "core",
    }
    if link:
        headers["link"] = link
    return httpx.Response(200, json=body, headers=headers)


def test_repository_payload_to_bronze_record_preserves_raw_payload_and_metadata() -> None:
    rate_limit = RateLimitSnapshot(
        limit=5000, remaining=4999, used=1, reset_epoch_seconds=123, resource="core"
    )

    record = repository_payload_to_bronze_record(
        tenant_id="sandbox",
        payload=repository_payload(),
        fetched_at=FETCHED_AT,
        ingestion_run_id="run-123",
        rate_limit=rate_limit,
    )

    assert record["tenant_id"] == "sandbox"
    assert record["source"] == "github"
    assert record["resource_type"] == "repositories"
    assert record["source_id"] == "MDEwOlJlcG9zaXRvcnkxMjk2MjY5"
    assert record["source_owner"] == "octocat"
    assert record["source_repo"] == "octocat/Hello-World"
    assert record["ingestion_run_id"] == "run-123"
    assert json.loads(record["payload_json"])["unexpected_future_field"] == {"kept": True}
    assert json.loads(record["rate_limit_json"])["remaining"] == 4999


def test_pull_request_payload_to_bronze_record_preserves_raw_payload_and_metadata() -> None:
    record = pull_request_payload_to_bronze_record(
        tenant_id="sandbox",
        payload=pull_request_payload(),
        fetched_at=FETCHED_AT,
        ingestion_run_id="run-pr",
        rate_limit=None,
    )

    assert record["tenant_id"] == "sandbox"
    assert record["resource_type"] == "pull_requests"
    assert record["source_id"] == "MDExOlB1bGxSZXF1ZXN0MQ=="
    assert record["source_owner"] == "octocat"
    assert record["source_repo"] == "octocat/Hello-World"
    assert json.loads(record["payload_json"])["base"]["repo"]["full_name"] == "octocat/Hello-World"


def test_github_client_follows_pagination_and_captures_rate_limits() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_paths.append(str(request.url))
        if str(request.url) == "https://api.github.test/users/octocat/repos?per_page=100":
            return response(
                [repository_payload("octocat/Repo-One")],
                link='<https://api.github.test/users/octocat/repos?page=2>; rel="next"',
                remaining="4998",
            )
        if str(request.url) == "https://api.github.test/users/octocat/repos?page=2":
            return response([repository_payload("octocat/Repo-Two")], remaining="4997")
        raise AssertionError(f"Unexpected request: {request.url}")

    with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
        client = GitHubRestClient(
            api_base_url="https://api.github.test", token="fake-token", client=http_client
        )
        items, rate_limits = client.get_paginated("/users/octocat/repos", params={"per_page": 100})

    assert [item["full_name"] for item in items] == ["octocat/Repo-One", "octocat/Repo-Two"]
    assert [rate_limit.remaining for rate_limit in rate_limits] == [4998, 4997]
    assert len(seen_paths) == 2


def test_ingest_tenant_github_to_bronze_writes_idempotent_delta_tables(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    request_counts: dict[str, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        request_counts[path] = request_counts.get(path, 0) + 1
        if path == "/users/octocat/repos":
            return response([repository_payload("octocat/Hello-World")], remaining="4998")
        if path == "/repos/octocat/Hello-World":
            return response(repository_payload("octocat/Hello-World"), remaining="4997")
        if path == "/repos/octocat/Hello-World/pulls":
            return response([pull_request_payload("octocat/Hello-World")], remaining="4996")
        raise AssertionError(f"Unexpected request: {request.url}")

    def run_ingestion(run_id: str) -> None:
        with httpx.Client(transport=httpx.MockTransport(handler)) as http_client:
            client = GitHubRestClient(
                api_base_url="https://api.github.test", token="fake-token", client=http_client
            )
            result = ingest_tenant_github_to_bronze(
                tenant_config(),
                token="fake-token",
                ingestion_run_id=run_id,
                fetched_at=FETCHED_AT,
                client=client,
            )
        assert result.repository_count == 1
        assert result.pull_request_count == 1
        assert len(result.rate_limits) == 3

    run_ingestion("run-one")
    run_ingestion("run-two")

    repositories_path = delta_table_path("sandbox", "bronze", "github", "repositories")
    pull_requests_path = delta_table_path("sandbox", "bronze", "github", "pull_requests")
    repository_rows = DeltaTable(str(repositories_path)).to_pyarrow_table().to_pylist()
    pull_request_rows = DeltaTable(str(pull_requests_path)).to_pyarrow_table().to_pylist()

    assert len(repository_rows) == 1
    assert len(pull_request_rows) == 1
    assert repository_rows[0]["ingestion_run_id"] == "run-two"
    assert pull_request_rows[0]["ingestion_run_id"] == "run-two"
    assert json.loads(repository_rows[0]["payload_json"])["full_name"] == "octocat/Hello-World"
    assert json.loads(pull_request_rows[0]["payload_json"])["number"] == 1347
    assert json.loads(pull_request_rows[0]["rate_limit_json"])["remaining"] == 4996
    assert (repositories_path / "_delta_log").exists()
    assert (pull_requests_path / "_delta_log").exists()
    assert request_counts["/users/octocat/repos"] == 2
    assert request_counts["/repos/octocat/Hello-World"] == 2
    assert request_counts["/repos/octocat/Hello-World/pulls"] == 2
