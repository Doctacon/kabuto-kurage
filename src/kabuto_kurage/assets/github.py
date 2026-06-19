"""Dagster assets for the GitHub-to-Delta local data flow."""

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetSpec,
    Definitions,
    MaterializeResult,
    MetadataValue,
    StaticPartitionsDefinition,
    define_asset_job,
    multi_asset,
)
from deltalake import DeltaTable

from kabuto_kurage.ingestion.github_bronze import (
    GITHUB_SOURCE,
    PULL_REQUEST_RESOURCE,
    REPOSITORY_RESOURCE,
    GitHubBronzeIngestionResult,
    RateLimitSnapshot,
    ingest_tenant_github_to_bronze,
)
from kabuto_kurage.observability import GitHubTableObservabilityConfig, observe_github_table
from kabuto_kurage.paths import data_root, delta_table_path
from kabuto_kurage.tenancy import load_tenant_registry, validate_tenant_id
from kabuto_kurage.transforms.github_gold import (
    PR_CYCLE_TIME_TABLE,
    PR_THROUGHPUT_DAILY_TABLE,
    GitHubGoldMetricResult,
    materialize_tenant_github_gold,
)
from kabuto_kurage.transforms.github_silver import (
    GitHubSilverTransformResult,
    materialize_tenant_github_silver,
)

GITHUB_BRONZE_REPOSITORIES = "github_bronze_repositories"
GITHUB_BRONZE_PULL_REQUESTS = "github_bronze_pull_requests"
GITHUB_SILVER_REPOSITORIES = "github_silver_repositories"
GITHUB_SILVER_PULL_REQUESTS = "github_silver_pull_requests"
GITHUB_GOLD_PR_THROUGHPUT_DAILY = "github_gold_pr_throughput_daily"
GITHUB_GOLD_PR_CYCLE_TIME = "github_gold_pr_cycle_time"
GITHUB_MAX_REPOSITORIES_ENV = "KABUTO_GITHUB_MAX_REPOSITORIES"


def tenant_partitions_def() -> StaticPartitionsDefinition:
    """Build a static tenant partition definition from the active tenant registry."""

    return StaticPartitionsDefinition(load_tenant_registry().tenant_ids)


TENANT_PARTITIONS = tenant_partitions_def()


def _asset_spec(
    name: str,
    *,
    layer: str,
    resource_type: str,
    description: str,
    deps: Iterable[str] = (),
) -> AssetSpec:
    return AssetSpec(
        key=AssetKey(name),
        deps=[AssetKey(dep) for dep in deps],
        group_name=f"github_{layer}",
        description=description,
        metadata={
            "source": GITHUB_SOURCE,
            "layer": layer,
            "resource_type": resource_type,
        },
    )


@multi_asset(
    specs=[
        _asset_spec(
            GITHUB_BRONZE_REPOSITORIES,
            layer="bronze",
            resource_type=REPOSITORY_RESOURCE,
            description="Raw GitHub repository payloads written to tenant-scoped bronze Delta.",
        ),
        _asset_spec(
            GITHUB_BRONZE_PULL_REQUESTS,
            layer="bronze",
            resource_type=PULL_REQUEST_RESOURCE,
            description="Raw GitHub pull request payloads written to tenant-scoped bronze Delta.",
        ),
    ],
    partitions_def=TENANT_PARTITIONS,
)
def github_bronze_assets(context: AssetExecutionContext) -> Iterable[MaterializeResult[None]]:
    """Ingest configured GitHub repositories and pull requests for one tenant partition."""

    tenant_id = _tenant_id_from_context(context)
    tenant = load_tenant_registry().get(tenant_id)
    result = ingest_tenant_github_to_bronze(
        tenant,
        max_repositories=_max_repositories_from_env(),
    )

    yield MaterializeResult(
        asset_key=GITHUB_BRONZE_REPOSITORIES,
        metadata=_bronze_metadata(
            result,
            resource_type=REPOSITORY_RESOURCE,
            row_count=result.repository_count,
        ),
    )
    yield MaterializeResult(
        asset_key=GITHUB_BRONZE_PULL_REQUESTS,
        metadata=_bronze_metadata(
            result,
            resource_type=PULL_REQUEST_RESOURCE,
            row_count=result.pull_request_count,
        ),
    )


@multi_asset(
    specs=[
        _asset_spec(
            GITHUB_SILVER_REPOSITORIES,
            layer="silver",
            resource_type=REPOSITORY_RESOURCE,
            description="Typed GitHub repository model derived from bronze Delta payloads.",
            deps=(GITHUB_BRONZE_REPOSITORIES, GITHUB_BRONZE_PULL_REQUESTS),
        ),
        _asset_spec(
            GITHUB_SILVER_PULL_REQUESTS,
            layer="silver",
            resource_type=PULL_REQUEST_RESOURCE,
            description="Typed GitHub pull request model derived from bronze Delta payloads.",
            deps=(GITHUB_BRONZE_REPOSITORIES, GITHUB_BRONZE_PULL_REQUESTS),
        ),
    ],
    partitions_def=TENANT_PARTITIONS,
)
def github_silver_assets(context: AssetExecutionContext) -> Iterable[MaterializeResult[None]]:
    """Build silver GitHub repository and pull request models for one tenant partition."""

    tenant_id = _tenant_id_from_context(context)
    result = materialize_tenant_github_silver(tenant_id)
    row_counts = {write.table_name: write.row_count for write in result.writes}

    yield MaterializeResult(
        asset_key=GITHUB_SILVER_REPOSITORIES,
        metadata=_silver_metadata(
            result,
            resource_type=REPOSITORY_RESOURCE,
            row_count=row_counts[REPOSITORY_RESOURCE],
        ),
    )
    yield MaterializeResult(
        asset_key=GITHUB_SILVER_PULL_REQUESTS,
        metadata=_silver_metadata(
            result,
            resource_type=PULL_REQUEST_RESOURCE,
            row_count=row_counts[PULL_REQUEST_RESOURCE],
        ),
    )


@multi_asset(
    specs=[
        _asset_spec(
            GITHUB_GOLD_PR_THROUGHPUT_DAILY,
            layer="gold",
            resource_type=PR_THROUGHPUT_DAILY_TABLE,
            description=(
                "Daily GitHub pull-request opened/merged/closed counts by tenant and repository."
            ),
            deps=(GITHUB_SILVER_PULL_REQUESTS,),
        ),
        _asset_spec(
            GITHUB_GOLD_PR_CYCLE_TIME,
            layer="gold",
            resource_type=PR_CYCLE_TIME_TABLE,
            description="Per-pull-request open-to-merge cycle time derived from silver GitHub PRs.",
            deps=(GITHUB_SILVER_PULL_REQUESTS,),
        ),
    ],
    partitions_def=TENANT_PARTITIONS,
)
def github_gold_assets(context: AssetExecutionContext) -> Iterable[MaterializeResult[None]]:
    """Build gold GitHub engineering metrics for one tenant partition."""

    tenant_id = _tenant_id_from_context(context)
    result = materialize_tenant_github_gold(tenant_id)
    row_counts = {write.table_name: write.row_count for write in result.writes}

    yield MaterializeResult(
        asset_key=GITHUB_GOLD_PR_THROUGHPUT_DAILY,
        metadata=_gold_metadata(
            result,
            resource_type=PR_THROUGHPUT_DAILY_TABLE,
            row_count=row_counts[PR_THROUGHPUT_DAILY_TABLE],
        ),
    )
    yield MaterializeResult(
        asset_key=GITHUB_GOLD_PR_CYCLE_TIME,
        metadata=_gold_metadata(
            result,
            resource_type=PR_CYCLE_TIME_TABLE,
            row_count=row_counts[PR_CYCLE_TIME_TABLE],
        ),
    )


github_assets_job = define_asset_job(
    name="github_assets_job",
    selection=[
        GITHUB_BRONZE_REPOSITORIES,
        GITHUB_BRONZE_PULL_REQUESTS,
        GITHUB_SILVER_REPOSITORIES,
        GITHUB_SILVER_PULL_REQUESTS,
        GITHUB_GOLD_PR_THROUGHPUT_DAILY,
        GITHUB_GOLD_PR_CYCLE_TIME,
    ],
)


def github_definitions() -> Definitions:
    """Return the Dagster definitions for the GitHub asset graph."""

    return Definitions(
        assets=[github_bronze_assets, github_silver_assets, github_gold_assets],
        jobs=[github_assets_job],
    )


def _tenant_id_from_context(context: AssetExecutionContext) -> str:
    return validate_tenant_id(context.partition_key)


def _max_repositories_from_env() -> int | None:
    configured = os.environ.get(GITHUB_MAX_REPOSITORIES_ENV)
    if configured is None or configured == "":
        return None
    try:
        value = int(configured)
    except ValueError as exc:
        raise ValueError(f"{GITHUB_MAX_REPOSITORIES_ENV} must be an integer when set") from exc
    if value < 1:
        raise ValueError(f"{GITHUB_MAX_REPOSITORIES_ENV} must be greater than zero when set")
    return value


def _bronze_metadata(
    result: GitHubBronzeIngestionResult,
    *,
    resource_type: str,
    row_count: int,
) -> dict[str, Any]:
    table_path = delta_table_path(result.tenant_id, "bronze", GITHUB_SOURCE, resource_type)
    metadata = _common_metadata(
        tenant_id=result.tenant_id,
        layer="bronze",
        resource_type=resource_type,
        table_path=table_path,
        row_count=row_count,
    )
    metadata.update(
        {
            "ingestion_run_id": result.ingestion_run_id,
            "fetched_at": result.fetched_at.isoformat(),
            "rate_limit_snapshots": len(result.rate_limits),
        }
    )
    min_remaining = _minimum_remaining_rate_limit(result.rate_limits)
    if min_remaining is not None:
        metadata["minimum_rate_limit_remaining"] = min_remaining
    return metadata


def _silver_metadata(
    result: GitHubSilverTransformResult,
    *,
    resource_type: str,
    row_count: int,
) -> dict[str, Any]:
    table_path = delta_table_path(result.tenant_id, "silver", GITHUB_SOURCE, resource_type)
    metadata = _common_metadata(
        tenant_id=result.tenant_id,
        layer="silver",
        resource_type=resource_type,
        table_path=table_path,
        row_count=row_count,
    )
    latest = _latest_silver_lineage(table_path)
    if latest["ingestion_run_id"]:
        metadata["latest_ingestion_run_id"] = latest["ingestion_run_id"]
    if latest["fetched_at"]:
        metadata["latest_fetched_at"] = latest["fetched_at"]
    return metadata


def _gold_metadata(
    result: GitHubGoldMetricResult,
    *,
    resource_type: str,
    row_count: int,
) -> dict[str, Any]:
    table_path = delta_table_path(result.tenant_id, "gold", GITHUB_SOURCE, resource_type)
    metadata = _common_metadata(
        tenant_id=result.tenant_id,
        layer="gold",
        resource_type=resource_type,
        table_path=table_path,
        row_count=row_count,
    )
    if resource_type == PR_THROUGHPUT_DAILY_TABLE:
        metadata["metric_grain"] = "tenant_repository_day"
        metadata["metric_counts"] = "opened_count,merged_count,closed_count"
    if resource_type == PR_CYCLE_TIME_TABLE:
        metadata["metric_grain"] = "pull_request"
        metadata["duration_unit"] = "hours_and_days"
    return metadata


def _common_metadata(
    *,
    tenant_id: str,
    layer: str,
    resource_type: str,
    table_path: Path,
    row_count: int,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "tenant_id": tenant_id,
        "source": GITHUB_SOURCE,
        "layer": layer,
        "resource_type": resource_type,
        "row_count": row_count,
        "delta_table_path": MetadataValue.path(str(table_path)),
        "data_root": MetadataValue.path(str(data_root())),
    }
    if table_path.exists():
        delta_table = DeltaTable(str(table_path))
        metadata["delta_version"] = delta_table.version()
    metadata.update(
        observe_github_table(
            tenant_id=tenant_id,
            config=GitHubTableObservabilityConfig(
                layer=layer,
                resource_type=resource_type,
                freshness_column=_freshness_column(layer, resource_type),
                ingestion_run_column=_ingestion_run_column(layer, resource_type),
                rate_limit_column=("rate_limit_json" if layer == "bronze" else None),
            ),
        ).as_dagster_metadata()
    )
    return metadata


def _freshness_column(layer: str, resource_type: str) -> str | None:
    if layer in {"bronze", "silver"}:
        return "fetched_at"
    if layer == "gold" and resource_type == PR_THROUGHPUT_DAILY_TABLE:
        return "latest_fetched_at"
    if layer == "gold" and resource_type == PR_CYCLE_TIME_TABLE:
        return "fetched_at"
    return None


def _ingestion_run_column(layer: str, resource_type: str) -> str | None:
    if layer in {"bronze", "silver"}:
        return "ingestion_run_id"
    if layer == "gold" and resource_type == PR_THROUGHPUT_DAILY_TABLE:
        return "latest_ingestion_run_id"
    if layer == "gold" and resource_type == PR_CYCLE_TIME_TABLE:
        return "ingestion_run_id"
    return None


def _latest_silver_lineage(table_path: Path) -> dict[str, str | None]:
    if not table_path.exists():
        return {"ingestion_run_id": None, "fetched_at": None}

    rows = DeltaTable(str(table_path)).to_pyarrow_table(
        columns=["ingestion_run_id", "fetched_at"]
    ).to_pylist()
    ingestion_run_ids = sorted(
        {
            str(row["ingestion_run_id"])
            for row in rows
            if row.get("ingestion_run_id") is not None
        }
    )
    fetched_values = sorted(
        {row["fetched_at"].isoformat() for row in rows if row.get("fetched_at") is not None}
    )
    return {
        "ingestion_run_id": ingestion_run_ids[-1] if ingestion_run_ids else None,
        "fetched_at": fetched_values[-1] if fetched_values else None,
    }


def _minimum_remaining_rate_limit(rate_limits: Iterable[RateLimitSnapshot]) -> int | None:
    remaining_values = [
        snapshot.remaining for snapshot in rate_limits if snapshot.remaining is not None
    ]
    if not remaining_values:
        return None
    return min(remaining_values)
