from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from deltalake import DeltaTable
from dlt.sources.helpers.rest_client import RESTClient
from dlt.sources.helpers.rest_client.paginators import HeaderLinkPaginator
from requests.adapters import BaseAdapter
from requests.models import PreparedRequest

from kabuto_kurage.ingestion.github_bronze import (
    DLT_BRONZE_SOURCE_NAME,
    GitHubDltSourceContext,
    GitHubRestClient,
    RateLimitSnapshot,
    build_github_bronze_dlt_source,
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


def response(
    request: PreparedRequest,
    body: object,
    *,
    link: str | None = None,
    remaining: str = "4999",
    status_code: int = 200,
) -> requests.Response:
    github_response = requests.Response()
    github_response.status_code = status_code
    github_response.url = request.url or ""
    github_response.request = request
    github_response.headers.update(
        {
            "content-type": "application/json",
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": remaining,
            "x-ratelimit-used": str(5000 - int(remaining)),
            "x-ratelimit-reset": "1781800000",
            "x-ratelimit-resource": "core",
        }
    )
    if link:
        github_response.headers["link"] = link
    github_response._content = json.dumps(body).encode("utf-8")
    return github_response


class GitHubMockAdapter(BaseAdapter):
    """Small requests adapter for deterministic dlt RESTClient tests."""

    def __init__(self, handler: Callable[[PreparedRequest], requests.Response]) -> None:
        self._handler = handler

    def send(
        self,
        request: PreparedRequest,
        stream: bool = False,
        timeout: float | tuple[float, float] | None = None,
        verify: bool | str = True,
        cert: bytes | str | tuple[bytes | str, bytes | str] | None = None,
        proxies: dict[str, str] | None = None,
    ) -> requests.Response:
        return self._handler(request)

    def close(self) -> None:
        return None


def github_session(handler: Callable[[PreparedRequest], requests.Response]) -> requests.Session:
    session = requests.Session()
    session.mount("https://api.github.test", GitHubMockAdapter(handler))
    return session


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


def test_github_client_uses_dlt_rest_client_and_header_link_paginator() -> None:
    client = GitHubRestClient(api_base_url="https://api.github.test", token="fake-token")

    try:
        assert client.dlt_backend_summary() == {
            "source": DLT_BRONZE_SOURCE_NAME,
            "client": RESTClient.__name__,
            "paginator": HeaderLinkPaginator.__name__,
        }
    finally:
        client.close()


def test_github_bronze_source_exposes_explicit_dlt_resources() -> None:
    session = github_session(lambda request: response(request, []))
    try:
        client = GitHubRestClient(
            api_base_url="https://api.github.test", token="fake-token", session=session
        )
        context = GitHubDltSourceContext(
            tenant=tenant_config(),
            source_config=tenant_config().github,
            client=client,
            ingestion_run_id="run-source",
            fetched_at=FETCHED_AT,
            max_repositories=1,
        )
        source = build_github_bronze_dlt_source(context)
    finally:
        session.close()

    assert source.name == DLT_BRONZE_SOURCE_NAME
    assert sorted(source.resources.keys()) == ["pull_requests", "repositories"]
    repository_schema = source.resources["repositories"].compute_table_schema()
    pull_request_schema = source.resources["pull_requests"].compute_table_schema()
    assert repository_schema["write_disposition"] == "replace"
    assert pull_request_schema["write_disposition"] == "replace"
    assert repository_schema["columns"]["tenant_id"]["data_type"] == "text"
    assert pull_request_schema["columns"]["payload_json"]["data_type"] == "text"


def test_github_client_follows_dlt_pagination_and_captures_rate_limits() -> None:
    seen_paths: list[str] = []

    def handler(request: PreparedRequest) -> requests.Response:
        seen_paths.append(str(request.url))
        if str(request.url) == "https://api.github.test/users/octocat/repos?per_page=100":
            return response(
                request,
                [repository_payload("octocat/Repo-One")],
                link='<https://api.github.test/users/octocat/repos?page=2>; rel="next"',
                remaining="4998",
            )
        if str(request.url) == "https://api.github.test/users/octocat/repos?page=2":
            return response(request, [repository_payload("octocat/Repo-Two")], remaining="4997")
        raise AssertionError(f"Unexpected request: {request.url}")

    session = github_session(handler)
    try:
        client = GitHubRestClient(
            api_base_url="https://api.github.test", token="fake-token", session=session
        )
        items, rate_limits = client.get_paginated("/users/octocat/repos", params={"per_page": 100})
    finally:
        session.close()

    assert [item["full_name"] for item in items] == ["octocat/Repo-One", "octocat/Repo-Two"]
    assert [rate_limit.remaining for rate_limit in rate_limits] == [4998, 4997]
    assert len(seen_paths) == 2


def test_ingest_tenant_github_to_bronze_writes_idempotent_delta_tables(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(tmp_path))
    request_counts: dict[str, int] = {}

    def handler(request: PreparedRequest) -> requests.Response:
        path = request.path_url.split("?", 1)[0]
        request_counts[path] = request_counts.get(path, 0) + 1
        if path == "/users/octocat/repos":
            return response(request, [repository_payload("octocat/Hello-World")], remaining="4998")
        if path == "/repos/octocat/Hello-World":
            return response(request, repository_payload("octocat/Hello-World"), remaining="4997")
        if path == "/repos/octocat/Hello-World/pulls":
            return response(
                request, [pull_request_payload("octocat/Hello-World")], remaining="4996"
            )
        raise AssertionError(f"Unexpected request: {request.url}")

    latest_result = None

    def run_ingestion(run_id: str) -> None:
        nonlocal latest_result
        session = github_session(handler)
        try:
            client = GitHubRestClient(
                api_base_url="https://api.github.test", token="fake-token", session=session
            )
            result = ingest_tenant_github_to_bronze(
                tenant_config(),
                token="fake-token",
                ingestion_run_id=run_id,
                fetched_at=FETCHED_AT,
                client=client,
            )
        finally:
            session.close()
        latest_result = result
        assert result.repository_count == 1
        assert result.pull_request_count == 1
        assert len(result.rate_limits) == 3
        assert result.dlt_artifacts.source_name == DLT_BRONZE_SOURCE_NAME
        assert set(result.dlt_artifacts.resource_names) == {"repositories", "pull_requests"}
        assert result.dlt_artifacts.schema_path.exists()
        assert result.dlt_artifacts.state_path.exists()
        assert "fake-token" not in json.dumps(result.as_dict())

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
    assert "fake-token" not in json.dumps(repository_rows, default=str)
    assert "fake-token" not in json.dumps(pull_request_rows, default=str)
    assert latest_result is not None
    dlt_schema = json.loads(latest_result.dlt_artifacts.schema_path.read_text(encoding="utf-8"))
    dlt_state = json.loads(latest_result.dlt_artifacts.state_path.read_text(encoding="utf-8"))
    assert set(dlt_state["resources"]) == {"repositories", "pull_requests"}
    assert dlt_state["resources"]["repositories"]["row_count"] == 1
    assert dlt_state["resources"]["pull_requests"]["latest_rate_limit"]["remaining"] == 4996
    assert set(dlt_schema["resource_schemas"]) == {"repositories", "pull_requests"}
    assert dlt_schema["resource_schemas"]["repositories"]["write_disposition"] == "replace"
    assert dlt_schema["resource_schemas"]["pull_requests"]["columns"]["payload_json"][
        "data_type"
    ] == "text"
    assert "fake-token" not in json.dumps(dlt_schema)
    assert "fake-token" not in json.dumps(dlt_state)
    assert (repositories_path / "_delta_log").exists()
    assert (pull_requests_path / "_delta_log").exists()
    assert request_counts["/users/octocat/repos"] == 2
    assert request_counts["/repos/octocat/Hello-World"] == 2
    assert request_counts["/repos/octocat/Hello-World/pulls"] == 2
