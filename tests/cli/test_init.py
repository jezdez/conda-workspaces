"""Tests for conda_workspaces.cli.init."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import pytest
import tomlkit

from conda_workspaces.cli.init import execute_init
from conda_workspaces.exceptions import ManifestExistsError

if TYPE_CHECKING:
    from pathlib import Path

_INIT_DEFAULTS = {
    "manifest_format": "pixi",
    "name": None,
    "channels": None,
    "platforms": ["linux-64", "osx-arm64", "win-64"],
}


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**{**_INIT_DEFAULTS, **kwargs})


@pytest.mark.parametrize(
    "fmt, filename",
    [
        ("pixi", "pixi.toml"),
        ("conda", "conda.toml"),
        ("pyproject", "pyproject.toml"),
    ],
    ids=["pixi-format", "conda-format", "pyproject-format"],
)
def test_init_creates_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fmt: str, filename: str
) -> None:
    monkeypatch.chdir(tmp_path)
    args = _make_args(manifest_format=fmt, name="my-project")
    result = execute_init(args)
    assert result == 0
    assert (tmp_path / filename).exists()


@pytest.mark.parametrize(
    "fmt, filename",
    [
        ("pixi", "pixi.toml"),
        ("conda", "conda.toml"),
    ],
    ids=["pixi-exists", "conda-exists"],
)
def test_init_refuses_overwrite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fmt: str,
    filename: str,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / filename).write_text("existing content", encoding="utf-8")
    args = _make_args(manifest_format=fmt, name="proj")
    with pytest.raises(ManifestExistsError, match="already exists"):
        execute_init(args)


def test_init_pixi_toml_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    args = _make_args(
        manifest_format="pixi",
        name="structured",
        channels=["conda-forge", "bioconda"],
        platforms=["linux-64"],
    )
    execute_init(args)
    doc = tomlkit.loads((tmp_path / "pixi.toml").read_text(encoding="utf-8"))
    assert doc["workspace"]["name"] == "structured"
    assert doc["workspace"]["channels"] == ["conda-forge", "bioconda"]
    assert doc["workspace"]["platforms"] == ["linux-64"]
    assert "dependencies" in doc


def test_init_conda_toml_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    args = _make_args(manifest_format="conda", name="my-conda")
    execute_init(args)
    doc = tomlkit.loads((tmp_path / "conda.toml").read_text(encoding="utf-8"))
    assert doc["workspace"]["name"] == "my-conda"


def test_init_pyproject_creates_tool_pixi(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    args = _make_args(manifest_format="pyproject", name="pp")
    execute_init(args)
    doc = tomlkit.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert "pixi" in doc["tool"]
    assert "workspace" in doc["tool"]["pixi"]


def test_init_pyproject_appends_to_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If pyproject.toml already exists, init adds [tool.pixi] to it."""
    monkeypatch.chdir(tmp_path)
    existing = '[project]\nname = "existing"\n'
    (tmp_path / "pyproject.toml").write_text(existing, encoding="utf-8")
    args = _make_args(manifest_format="pyproject", name="pp")
    execute_init(args)
    doc = tomlkit.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert doc["project"]["name"] == "existing"
    assert "pixi" in doc["tool"]


def test_init_pyproject_refuses_existing_pixi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    existing = '[tool.pixi.workspace]\nchannels = ["defaults"]\n'
    (tmp_path / "pyproject.toml").write_text(existing, encoding="utf-8")
    args = _make_args(manifest_format="pyproject", name="pp")
    with pytest.raises(ManifestExistsError, match="already exists"):
        execute_init(args)


def test_init_default_name_from_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    args = _make_args(manifest_format="pixi", name=None)
    execute_init(args)
    doc = tomlkit.loads((tmp_path / "pixi.toml").read_text(encoding="utf-8"))
    assert doc["workspace"]["name"] == tmp_path.name


def test_init_default_channels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    args = _make_args(manifest_format="pixi", name="ch-test", channels=None)
    execute_init(args)
    doc = tomlkit.loads((tmp_path / "pixi.toml").read_text(encoding="utf-8"))
    assert doc["workspace"]["channels"] == ["conda-forge"]
