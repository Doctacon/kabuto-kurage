from __future__ import annotations

from pathlib import Path

IAC_ROOT = Path("iac/local")


def read_iac_texts() -> str:
    text_paths = [
        path
        for path in IAC_ROOT.rglob("*")
        if path.is_file()
        and ".terraform" not in path.parts
        and path.name != "terraform.tfstate"
        and path.suffix in {".tf", ".hcl", ".yml", ".md", ".tftpl"}
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in text_paths)


def test_local_iac_files_exist_with_clear_entrypoints() -> None:
    expected_paths = [
        IAC_ROOT / "versions.tf",
        IAC_ROOT / "variables.tf",
        IAC_ROOT / "main.tf",
        IAC_ROOT / "outputs.tf",
        IAC_ROOT / "docker-compose.yml",
        IAC_ROOT / "README.md",
        IAC_ROOT / "templates" / "dagster.yaml.tftpl",
        IAC_ROOT / "templates" / "kabuto.env.tftpl",
        Path("docs/local-iac.md"),
    ]

    for path in expected_paths:
        assert path.exists(), f"Missing local IaC file: {path}"


def test_terraform_is_local_only_and_does_not_define_cloud_resources() -> None:
    iac_text = read_iac_texts().lower()

    assert 'source  = "hashicorp/local"' in iac_text
    assert 'resource "local_file"' in iac_text

    forbidden_markers = [
        "hashicorp/aws",
        "hashicorp/google",
        "hashicorp/azurerm",
        "kubernetes_",
        "aws_",
        "google_",
        "azurerm_",
    ]
    for marker in forbidden_markers:
        assert marker not in iac_text


def test_local_iac_templates_do_not_commit_or_generate_secret_values() -> None:
    env_template = (IAC_ROOT / "templates" / "kabuto.env.tftpl").read_text(encoding="utf-8")
    readme = (IAC_ROOT / "README.md").read_text(encoding="utf-8")

    assert "GITHUB_TOKEN=" not in env_template
    assert "GH_TOKEN=" not in env_template
    assert "contains no GitHub token value" in env_template
    assert "Do not put token values" in readme


def test_docker_compose_is_optional_dagster_runner_not_test_requirement() -> None:
    compose = (IAC_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

    assert "dagster" in compose
    assert "uv run dagster dev" in compose
    assert "../../.local/runtime/kabuto.env" in compose
    assert "GITHUB_TOKEN: ${GITHUB_TOKEN:-}" in compose
    assert "GH_TOKEN: ${GH_TOKEN:-}" in compose
