"""Minimal local MCP wrapper for tenant-scoped GitHub engineering metrics.

The MCP tools intentionally share the same local token allowlist and query layer as the
REST export API. Token values are accepted as tool inputs only for local auth checks and
are never returned in tool responses.
"""

from __future__ import annotations

from typing import Literal, cast

from mcp.server.fastmcp import FastMCP

from kabuto_kurage.api.auth import require_tenant_access
from kabuto_kurage.queries.github_metrics import (
    DEFAULT_EXPORT_LIMIT,
    DateFilter,
    RepositoryFilter,
    query_pr_cycle_time,
    query_pr_throughput_daily,
    summarize_github_metrics,
)

MCP_SERVER_NAME = "kabuto-kurage-engineering-metrics"
MCP_TOOL_NAMES = (
    "github_pr_throughput_daily",
    "github_pr_cycle_time",
    "github_metrics_summary",
)
TransportName = Literal["stdio", "streamable-http", "sse"]


def github_pr_throughput_daily(
    *,
    tenant_id: str,
    api_token: str,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_name: RepositoryFilter = None,
    limit: int | None = DEFAULT_EXPORT_LIMIT,
    offset: int = 0,
) -> list[dict[str, object]]:
    """Return tenant-scoped daily GitHub PR throughput rows.

    Args:
        tenant_id: Explicit tenant ID to query.
        api_token: Local export API token allowed for the requested tenant.
        start_date: Optional inclusive YYYY-MM-DD filter on metric_date.
        end_date: Optional inclusive YYYY-MM-DD filter on metric_date.
        repository_full_name: Optional repository full-name filter or list of filters.
        limit: Optional positive row limit, matching the REST/query contract.
        offset: Optional non-negative row offset, matching the REST/query contract.
    """

    _authorize_tool_call(tenant_id=tenant_id, api_token=api_token)
    return cast(
        list[dict[str, object]],
        query_pr_throughput_daily(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            repository_full_names=repository_full_name,
            limit=limit,
            offset=offset,
        ),
    )


def github_pr_cycle_time(
    *,
    tenant_id: str,
    api_token: str,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_name: RepositoryFilter = None,
    merged: bool | None = None,
    limit: int | None = DEFAULT_EXPORT_LIMIT,
    offset: int = 0,
) -> list[dict[str, object]]:
    """Return tenant-scoped GitHub PR cycle-time rows.

    Args:
        tenant_id: Explicit tenant ID to query.
        api_token: Local export API token allowed for the requested tenant.
        start_date: Optional inclusive YYYY-MM-DD filter on created_at.
        end_date: Optional inclusive YYYY-MM-DD filter on created_at.
        repository_full_name: Optional repository full-name filter or list of filters.
        merged: Optional filter for merged or unmerged pull requests.
        limit: Optional positive row limit, matching the REST/query contract.
        offset: Optional non-negative row offset, matching the REST/query contract.
    """

    _authorize_tool_call(tenant_id=tenant_id, api_token=api_token)
    return cast(
        list[dict[str, object]],
        query_pr_cycle_time(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            repository_full_names=repository_full_name,
            merged=merged,
            limit=limit,
            offset=offset,
        ),
    )


def github_metrics_summary(
    *,
    tenant_id: str,
    api_token: str,
    start_date: DateFilter = None,
    end_date: DateFilter = None,
    repository_full_name: RepositoryFilter = None,
) -> dict[str, object]:
    """Return a compact tenant-scoped GitHub metrics summary.

    Args:
        tenant_id: Explicit tenant ID to query.
        api_token: Local export API token allowed for the requested tenant.
        start_date: Optional inclusive YYYY-MM-DD filter.
        end_date: Optional inclusive YYYY-MM-DD filter.
        repository_full_name: Optional repository full-name filter or list of filters.
    """

    _authorize_tool_call(tenant_id=tenant_id, api_token=api_token)
    return cast(
        dict[str, object],
        summarize_github_metrics(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            repository_full_names=repository_full_name,
        ).as_dict(),
    )


def create_mcp_server() -> FastMCP:
    """Create the local MCP server with exactly the initial metric tools."""

    server = FastMCP(MCP_SERVER_NAME, json_response=True)
    server.tool(name="github_pr_throughput_daily")(github_pr_throughput_daily)
    server.tool(name="github_pr_cycle_time")(github_pr_cycle_time)
    server.tool(name="github_metrics_summary")(github_metrics_summary)
    return server


def _authorize_tool_call(*, tenant_id: str, api_token: str) -> None:
    require_tenant_access(tenant_id, f"Bearer {api_token}" if api_token else None)


mcp = create_mcp_server()


if __name__ == "__main__":
    mcp.run(transport="stdio")
