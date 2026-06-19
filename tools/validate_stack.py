"""Validate the initial local data-platform stack choices.

Run from the repository root with:

    uv run --with deltalake --with pyarrow --with dagster --with dlt \
      python tools/validate_stack.py

This is intentionally a narrow proof, not the project scaffold. It verifies:
- Python can write/read a local Delta table via delta-rs (`deltalake`).
- DuckDB can scan a local Delta table via the `delta` extension and `delta_scan`.
- GitHub API token setup is either usable through dlt REST helpers or reported as missing.
- Dagster can materialize a toy asset that writes and reads Delta storage.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

import duckdb
import pyarrow as pa
from dagster import MaterializeResult, MetadataValue, asset, materialize
from deltalake import DeltaTable, write_deltalake
from dlt.sources.helpers.rest_client.auth import BearerTokenAuth
from dlt.sources.helpers.rest_client.client import RESTClient


def _delta_rows() -> pa.Table:
    return pa.table(
        {
            "tenant_id": ["tenant_alpha", "tenant_alpha"],
            "source": ["stack_validation", "stack_validation"],
            "resource_type": ["toy_event", "toy_event"],
            "source_id": ["evt_1", "evt_2"],
            "payload_json": [
                json.dumps({"action": "opened", "number": 1}),
                json.dumps({"action": "closed", "number": 2}),
            ],
        }
    )


def validate_delta_read_write(base_dir: Path) -> dict[str, Any]:
    table_path = base_dir / "delta" / "bronze_github_events"
    write_deltalake(str(table_path), _delta_rows(), mode="overwrite")

    delta_table = DeltaTable(str(table_path))
    rows = delta_table.to_pyarrow_table().to_pylist()
    log_files = sorted((table_path / "_delta_log").glob("*.json"))

    assert len(rows) == 2, rows
    assert rows[0]["tenant_id"] == "tenant_alpha", rows
    assert log_files, "Delta transaction log JSON file was not created"

    return {
        "status": "passed",
        "path": str(table_path),
        "rows": len(rows),
        "version": delta_table.version(),
        "delta_log_files": [p.name for p in log_files],
    }


def validate_duckdb_delta_scan(base_dir: Path) -> dict[str, Any]:
    """Validate DuckDB can query a local Delta table through delta_scan."""

    table_path = base_dir / "duckdb" / "toy_delta_scan"
    write_deltalake(str(table_path), _delta_rows(), mode="overwrite")

    connection = duckdb.connect(database=":memory:")
    try:
        connection.execute("INSTALL delta")
        connection.execute("LOAD delta")
        result = connection.execute(
            """
            SELECT tenant_id, count(*) AS row_count
            FROM delta_scan(?)
            GROUP BY tenant_id
            """,
            [str(table_path)],
        ).fetchone()
    finally:
        connection.close()

    assert result == ("tenant_alpha", 2), result
    return {
        "status": "passed",
        "path": str(table_path),
        "extensions": ["delta"],
        "scan_function": "delta_scan",
        "tenant_id": result[0],
        "rows": result[1],
    }


def validate_github_api() -> dict[str, Any]:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return {
            "status": "skipped_missing_token",
            "setup": "Set GITHUB_TOKEN or GH_TOKEN to validate authenticated GitHub API access.",
        }

    client = RESTClient(
        base_url="https://api.github.com/",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "kabuto-kurage-stack-validation",
        },
        auth=BearerTokenAuth(token),
    )
    try:
        response = client.get("/rate_limit", timeout=10.0)
        response.raise_for_status()
        body = response.json()
    finally:
        client.session.close()
    core = body.get("resources", {}).get("core", {})
    return {
        "status": "passed",
        "limit": core.get("limit"),
        "remaining": core.get("remaining"),
        "reset": core.get("reset"),
    }


def validate_dagster_delta_asset(base_dir: Path) -> dict[str, Any]:
    table_path = base_dir / "dagster" / "toy_asset_delta"

    @asset(name="toy_delta_stack_validation")
    def toy_delta_stack_validation() -> MaterializeResult:
        write_deltalake(str(table_path), _delta_rows(), mode="overwrite")
        rows = DeltaTable(str(table_path)).to_pyarrow_table().num_rows
        return MaterializeResult(
            metadata={
                "delta_table_path": MetadataValue.path(str(table_path)),
                "row_count": rows,
            }
        )

    result = materialize([toy_delta_stack_validation], raise_on_error=True)
    assert result.success, "Dagster materialization did not report success"
    rows = DeltaTable(str(table_path)).to_pyarrow_table().num_rows
    assert rows == 2, rows

    return {
        "status": "passed",
        "asset": "toy_delta_stack_validation",
        "rows": rows,
        "path": str(table_path),
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="kabuto-kurage-stack-") as tmp:
        base_dir = Path(tmp)
        report = {
            "python": {
                "runtime": "python3",
                "package_runner": "uv run --with ...",
            },
            "delta": validate_delta_read_write(base_dir),
            "duckdb_delta": validate_duckdb_delta_scan(base_dir),
            "github": validate_github_api(),
            "dagster": validate_dagster_delta_asset(base_dir),
        }

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
