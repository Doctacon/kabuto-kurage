"""FastAPI app exposing tenant-scoped GitHub engineering metric exports."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, Header, Query, status
from fastapi.responses import JSONResponse

from kabuto_kurage.api.auth import (
    APIAuthConfigError,
    APIAuthError,
    APIPrincipal,
    TenantAccessDeniedError,
    require_tenant_access,
)
from kabuto_kurage.queries.github_metrics import (
    DEFAULT_EXPORT_LIMIT,
    MAX_EXPORT_LIMIT,
    GitHubMetricsQueryError,
    JsonObject,
    query_pr_cycle_time,
    query_pr_throughput_daily,
    summarize_github_metrics,
)
from kabuto_kurage.tenancy import TenantConfigError

RepositoryQuery = Annotated[
    list[str] | None,
    Query(
        alias="repository_full_name",
        description="Repeatable GitHub repository full-name filter",
    ),
]
LimitQuery = Annotated[
    int | None,
    Query(gt=0, le=MAX_EXPORT_LIMIT, description="Maximum rows to return"),
]
OffsetQuery = Annotated[int, Query(ge=0, description="Zero-based row offset")]
DateQuery = Annotated[str | None, Query(pattern=r"^\d{4}-\d{2}-\d{2}$")]
MergedQuery = Annotated[bool | None, Query(description="Filter cycle-time rows by merge state")]
AuthorizationHeader = Annotated[str | None, Header(alias="Authorization")]


def create_app() -> FastAPI:
    """Create the local export API application."""

    api = FastAPI(
        title="Kabuto Kurage Engineering Metrics API",
        version="0.1.0",
        description="Local tenant-scoped REST API over GitHub gold engineering metrics.",
    )

    @api.exception_handler(APIAuthError)
    async def api_auth_error_handler(_request: object, exc: APIAuthError) -> JSONResponse:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error="unauthorized",
            message=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @api.exception_handler(TenantAccessDeniedError)
    async def tenant_access_denied_handler(
        _request: object, exc: TenantAccessDeniedError
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_403_FORBIDDEN,
            error="forbidden",
            message=str(exc),
        )

    @api.exception_handler(APIAuthConfigError)
    async def api_auth_config_error_handler(
        _request: object, exc: APIAuthConfigError
    ) -> JSONResponse:
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            error="auth_config_error",
            message=str(exc),
        )

    @api.exception_handler(TenantConfigError)
    async def tenant_config_error_handler(_request: object, exc: TenantConfigError) -> JSONResponse:
        return _error_response(
            status.HTTP_400_BAD_REQUEST,
            error="invalid_tenant",
            message=str(exc),
        )

    @api.exception_handler(GitHubMetricsQueryError)
    async def query_error_handler(_request: object, exc: GitHubMetricsQueryError) -> JSONResponse:
        http_status = (
            status.HTTP_404_NOT_FOUND
            if "does not exist" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        return _error_response(http_status, error="query_error", message=str(exc))

    @api.get("/healthz", response_model=None)
    def healthz() -> JsonObject:
        return {"status": "ok"}

    @api.get(
        "/api/v1/tenants/{tenant_id}/metrics/github/pr-throughput-daily",
        response_model=None,
    )
    def get_pr_throughput_daily(
        tenant_id: str,
        _principal: Annotated[APIPrincipal, Depends(_require_authorized_tenant)],
        start_date: DateQuery = None,
        end_date: DateQuery = None,
        repository_full_name: RepositoryQuery = None,
        limit: LimitQuery = DEFAULT_EXPORT_LIMIT,
        offset: OffsetQuery = 0,
    ) -> list[JsonObject]:
        return query_pr_throughput_daily(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            repository_full_names=repository_full_name,
            limit=limit,
            offset=offset,
        )

    @api.get(
        "/api/v1/tenants/{tenant_id}/metrics/github/pr-cycle-time",
        response_model=None,
    )
    def get_pr_cycle_time(
        tenant_id: str,
        _principal: Annotated[APIPrincipal, Depends(_require_authorized_tenant)],
        start_date: DateQuery = None,
        end_date: DateQuery = None,
        repository_full_name: RepositoryQuery = None,
        merged: MergedQuery = None,
        limit: LimitQuery = DEFAULT_EXPORT_LIMIT,
        offset: OffsetQuery = 0,
    ) -> list[JsonObject]:
        return query_pr_cycle_time(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            repository_full_names=repository_full_name,
            merged=merged,
            limit=limit,
            offset=offset,
        )

    @api.get("/api/v1/tenants/{tenant_id}/metrics/github/summary", response_model=None)
    def get_github_metrics_summary(
        tenant_id: str,
        _principal: Annotated[APIPrincipal, Depends(_require_authorized_tenant)],
        start_date: DateQuery = None,
        end_date: DateQuery = None,
        repository_full_name: RepositoryQuery = None,
    ) -> JsonObject:
        return summarize_github_metrics(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            repository_full_names=repository_full_name,
        ).as_dict()

    return api


def _require_authorized_tenant(
    tenant_id: str,
    authorization: AuthorizationHeader = None,
) -> APIPrincipal:
    return require_tenant_access(tenant_id, authorization)


def _error_response(
    http_status: int,
    *,
    error: str,
    message: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"detail": {"error": error, "message": message}},
        headers=headers,
    )


app = create_app()
