from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

TASKFILE = Path("Taskfile.yml")
README = Path("README.md")
DEVELOPMENT = Path("docs/development.md")
TOOLS = Path("tools")

EXPECTED_TASKS = {
    "setup",
    "sync",
    "test",
    "lint",
    "typecheck",
    "validate",
    "validate-stack",
    "dagster",
    "materialize",
    "ingest",
    "silver",
    "gold",
    "observe",
    "api",
    "mcp",
}


def load_taskfile() -> dict[str, Any]:
    return yaml.safe_load(TASKFILE.read_text(encoding="utf-8"))


def task_commands(task: dict[str, Any]) -> list[str]:
    commands = task.get("cmds", [])
    result: list[str] = []
    for command in commands:
        if isinstance(command, str):
            result.append(command)
        elif isinstance(command, dict) and "cmd" in command:
            result.append(str(command["cmd"]))
    return result


def all_task_commands(taskfile: dict[str, Any]) -> str:
    commands: list[str] = []
    for task in taskfile["tasks"].values():
        if isinstance(task, dict):
            commands.extend(task_commands(task))
    return "\n".join(commands)


def test_taskfile_defines_documented_common_tasks() -> None:
    taskfile = load_taskfile()

    assert taskfile["version"] == "3"
    assert EXPECTED_TASKS <= set(taskfile["tasks"])
    for task_name in EXPECTED_TASKS:
        assert taskfile["tasks"][task_name].get("desc"), task_name


def test_taskfile_validation_wraps_uv_commands() -> None:
    validate_commands = task_commands(load_taskfile()["tasks"]["validate"])

    assert validate_commands == [
        "uv run pytest",
        "uv run ruff check .",
        "uv run mypy src",
    ]


def test_taskfile_supports_tenant_parameterized_pipeline_tasks() -> None:
    taskfile = load_taskfile()
    commands = all_task_commands(taskfile)

    assert "TENANT" in taskfile["vars"]
    assert "{{.tenant | default \"sandbox\"}}" == taskfile["vars"]["TENANT"]
    for task_name in ["ingest", "silver", "gold", "observe", "materialize"]:
        assert "{{.TENANT}}" in "\n".join(task_commands(taskfile["tasks"][task_name]))

    assert "tools/ingest_github_bronze.py" in commands
    assert "tools/build_github_silver.py" in commands
    assert "tools/build_github_gold.py" in commands
    assert "tools/observe_github.py" in commands


def test_taskfile_does_not_echo_secret_values() -> None:
    commands = all_task_commands(load_taskfile())
    forbidden_command_fragments = [
        "echo $GITHUB_TOKEN",
        "echo ${GITHUB_TOKEN}",
        "echo $GH_TOKEN",
        "echo ${GH_TOKEN}",
        "echo $KABUTO_R2_SECRET_ACCESS_KEY",
        "echo ${KABUTO_R2_SECRET_ACCESS_KEY}",
    ]

    for fragment in forbidden_command_fragments:
        assert fragment not in commands


def test_docs_teach_taskfile_as_primary_workflow_and_scripts_remain() -> None:
    docs = "\n".join(
        [README.read_text(encoding="utf-8"), DEVELOPMENT.read_text(encoding="utf-8")]
    )

    required_phrases = [
        "Taskfile as the primary workflow",
        "Taskfile is the primary human-facing command surface",
        "task setup",
        "task validate",
        "task ingest tenant=sandbox",
        "task api",
        "task mcp",
        "Python scripts in `tools/` remain available",
        "Proton Pass",
    ]
    for phrase in required_phrases:
        assert phrase in docs

    for script_name in [
        "ingest_github_bronze.py",
        "build_github_silver.py",
        "build_github_gold.py",
        "observe_github.py",
        "validate_stack.py",
    ]:
        assert (TOOLS / script_name).exists()
