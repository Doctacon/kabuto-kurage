from __future__ import annotations

import os
import subprocess
from pathlib import Path

from deltalake import DeltaTable

from kabuto_kurage.paths import delta_table_path


def test_dagster_cli_materializes_full_asset_chain_in_fixture_mode(
    monkeypatch, tmp_path: Path
) -> None:
    dagster_home = tmp_path / "dagster"
    data_root = tmp_path / "data"
    tenants_config = tmp_path / "tenants.yaml"
    dagster_home.mkdir()
    tenants_config.write_text(
        "tenants:\n"
        "  - tenant_id: sandbox\n"
        "    display_name: Sandbox Fixture\n"
        "    sources:\n"
        "      github:\n"
        "        token_env: GITHUB_TOKEN\n"
        "        api_base_url: https://api.github.com\n"
        "        owners: []\n"
        "        repositories:\n"
        "          - octocat/Hello-World\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(data_root))
    env = {
        **os.environ,
        "DAGSTER_HOME": str(dagster_home),
        "KABUTO_DATA_ROOT": str(data_root),
        "KABUTO_TENANTS_CONFIG": str(tenants_config),
        "KABUTO_GITHUB_FIXTURE_MODE": "1",
    }
    env.pop("GITHUB_TOKEN", None)
    env.pop("GH_TOKEN", None)

    result = subprocess.run(
        [
            "uv",
            "run",
            "dagster",
            "asset",
            "materialize",
            "-m",
            "kabuto_kurage.definitions",
            "--partition",
            "sandbox",
            "--select",
            "github_bronze_repositories,github_bronze_pull_requests,github_silver_repositories,github_silver_pull_requests,github_gold_pr_throughput_daily,github_gold_pr_cycle_time",
        ],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert "RUN_SUCCESS" in result.stdout
    assert "GitHub token not found" not in result.stdout

    expected_tables = [
        ("bronze", "repositories"),
        ("bronze", "pull_requests"),
        ("silver", "repositories"),
        ("silver", "pull_requests"),
        ("gold", "pr_throughput_daily"),
        ("gold", "pr_cycle_time"),
    ]
    for layer, table_name in expected_tables:
        table_path = delta_table_path("sandbox", layer, "github", table_name)
        assert (table_path / "_delta_log").exists(), table_path
        assert DeltaTable(str(table_path)).to_pyarrow_table().num_rows >= 1

    assert (data_root / "dlt" / "github" / "sandbox" / "schema.json").exists()
    assert (data_root / "dlt" / "github" / "sandbox" / "state.json").exists()
