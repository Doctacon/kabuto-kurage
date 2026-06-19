from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, cast


def _load_validate_stack_function() -> Any:
    module_path = Path("tools/validate_stack.py")
    spec = importlib.util.spec_from_file_location("validate_stack", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_duckdb_delta_scan


validate_duckdb_delta_scan = cast(Any, _load_validate_stack_function())


def test_validate_stack_proves_duckdb_delta_scan_over_local_delta(tmp_path: Path) -> None:
    result = validate_duckdb_delta_scan(tmp_path)

    assert result == {
        "status": "passed",
        "path": str(tmp_path / "duckdb" / "toy_delta_scan"),
        "extensions": ["delta"],
        "scan_function": "delta_scan",
        "tenant_id": "tenant_alpha",
        "rows": 2,
    }
    assert (tmp_path / "duckdb" / "toy_delta_scan" / "_delta_log").exists()
