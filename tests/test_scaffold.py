from pathlib import Path

from kabuto_kurage import __version__
from kabuto_kurage.paths import PROJECT_ROOT, data_root, delta_root


def test_package_has_initial_version() -> None:
    assert __version__ == "0.1.0"


def test_default_data_paths_stay_under_ignored_local_directory(monkeypatch) -> None:
    monkeypatch.delenv("KABUTO_DATA_ROOT", raising=False)

    assert data_root() == PROJECT_ROOT / ".local" / "data"
    assert delta_root() == PROJECT_ROOT / ".local" / "data" / "delta"


def test_data_root_can_be_overridden(monkeypatch, tmp_path: Path) -> None:
    configured_root = tmp_path / "kabuto-data"
    monkeypatch.setenv("KABUTO_DATA_ROOT", str(configured_root))

    assert data_root() == configured_root.resolve()
    assert delta_root() == configured_root.resolve() / "delta"
