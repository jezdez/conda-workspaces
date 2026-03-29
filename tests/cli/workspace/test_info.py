"""Tests for conda_workspaces.cli.workspace.info."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from conda_workspaces.cli.workspace.info import execute_info

from ..conftest import make_args

if TYPE_CHECKING:
    from pathlib import Path

    from rich.console import Console

    from tests.conftest import CreateWorkspaceEnv

_DEFAULTS = {"file": None, "environment": None, "json": False}


def test_info_workspace_overview(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    rich_console: Console,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS)
    result = execute_info(args, console=rich_console)
    assert result == 0
    out = rich_console.file.getvalue()
    assert "Manifest" in out
    assert "Environments" in out
    assert "default" in out
    assert "test" in out
    assert "conda-forge" in out


@pytest.mark.parametrize(
    "env_name, expected_fragments",
    [
        (
            "default",
            ["Environment", "default", "Installed", "no", "conda-forge", "python"],
        ),
        (
            "test",
            ["Environment", "test", "python", "pytest"],
        ),
    ],
    ids=["default-text", "named-env"],
)
def test_info_env_details(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    rich_console: Console,
    env_name: str,
    expected_fragments: list[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS, environment=env_name)
    result = execute_info(args, console=rich_console)
    assert result == 0
    out = rich_console.file.getvalue()
    for fragment in expected_fragments:
        assert fragment in out


def test_info_installed_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    rich_console: Console,
    tmp_workspace_env: CreateWorkspaceEnv,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    tmp_workspace_env(pixi_workspace, "default", pkg_count=3)

    args = make_args(_DEFAULTS, environment="default")
    execute_info(args, console=rich_console)
    out = rich_console.file.getvalue()
    assert "Installed" in out and "yes" in out
    assert "Packages" in out and "3" in out


def test_info_json_workspace(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    rich_console: Console,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS, json=True)
    execute_info(args, console=rich_console)
    out = rich_console.file.getvalue()
    data = json.loads(out)
    assert data["name"] == "cli-test"
    assert "environments" in data
    assert "channels" in data


def test_info_json_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    rich_console: Console,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS, environment="default", json=True)
    execute_info(args, console=rich_console)
    out = rich_console.file.getvalue()
    data = json.loads(out)
    assert data["name"] == "default"
    assert "conda_dependencies" in data
    assert "channels" in data


def test_info_shows_pypi_dependencies(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rich_console: Console,
) -> None:
    """PyPI dependencies appear in text output."""
    content = """\
[workspace]
name = "pypi-info"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[dependencies]
python = ">=3.10"

[pypi-dependencies]
requests = ">=2.28"
"""
    (tmp_path / "pixi.toml").write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    args = make_args(_DEFAULTS, environment="default")
    execute_info(args, console=rich_console)
    out = rich_console.file.getvalue()
    assert "PyPI dependencies" in out
    assert "requests" in out
