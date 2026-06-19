"""Shared local filesystem paths for the portfolio data platform.

The scaffold keeps runtime data under ignored local directories by default. Later tickets
will hang Delta Lake bronze/silver/gold paths and Dagster resources off these helpers.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def data_root() -> Path:
    """Return the root directory for generated local data."""

    configured = os.environ.get("KABUTO_DATA_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return PROJECT_ROOT / ".local" / "data"


def delta_root() -> Path:
    """Return the local root where Delta tables should be written."""

    return data_root() / "delta"
