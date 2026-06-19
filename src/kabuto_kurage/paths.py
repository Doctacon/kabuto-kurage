"""Shared local filesystem paths for the portfolio data platform.

Runtime data stays under ignored local directories by default. Tenant-scoped Delta paths
make the local multi-tenancy model visible before any ingestion code exists.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DELTA_LAYERS = ("bronze", "silver", "gold")


def data_root() -> Path:
    """Return the root directory for generated local data."""

    configured = os.environ.get("KABUTO_DATA_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return PROJECT_ROOT / ".local" / "data"


def delta_root() -> Path:
    """Return the local root where Delta tables should be written."""

    return data_root() / "delta"


def tenant_delta_root(tenant_id: str) -> Path:
    """Return the root Delta path for one tenant."""

    from kabuto_kurage.tenancy import validate_tenant_id

    return delta_root() / "tenants" / validate_tenant_id(tenant_id)


def delta_layer_root(tenant_id: str, layer: str) -> Path:
    """Return the Delta path for one tenant and lakehouse layer."""

    if layer not in DELTA_LAYERS:
        raise ValueError(f"Delta layer must be one of {DELTA_LAYERS}: {layer}")
    return tenant_delta_root(tenant_id) / layer


def delta_table_path(tenant_id: str, layer: str, source: str, table_name: str) -> Path:
    """Return the conventional Delta table path for tenant/source/table data.

    Shape: `.local/data/delta/tenants/{tenant_id}/{layer}/{source}/{table_name}`.
    """

    _validate_path_segment(source, field="source")
    _validate_path_segment(table_name, field="table_name")
    return delta_layer_root(tenant_id, layer) / source / table_name


def _validate_path_segment(value: str, *, field: str) -> str:
    if not value or "/" in value or value in {".", ".."}:
        raise ValueError(f"{field} must be a non-empty single path segment")
    return value
