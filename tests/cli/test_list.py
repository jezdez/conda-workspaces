"""Tests for conda_workspaces.cli.list."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from conda_workspaces.cli.list import execute_list

from .conftest import make_args

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import CreateWorkspaceEnv

_DEFAULTS = {
    "file": None,
    "installed": False,
    "json": False,
    "envs": False,
    "environment": "default",
}


def test_list_all_environments(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS,envs=True)
    result = execute_list(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "default" in out
    assert "test" in out


def test_list_installed_only(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS,envs=True, installed=True)
    result = execute_list(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "No environments found" in out


def test_list_installed_with_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_workspace_env: CreateWorkspaceEnv,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    tmp_workspace_env(pixi_workspace, "default")

    args = make_args(_DEFAULTS,envs=True, installed=True)
    execute_list(args)
    out = capsys.readouterr().out
    assert "default" in out
    assert "test" not in out


def test_list_json_output(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS,envs=True, json=True)
    execute_list(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    names = {row["name"] for row in data}
    assert "default" in names
    assert "test" in names


def test_list_packages_not_installed(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default list (packages) raises when the env is not installed."""
    from conda_workspaces.exceptions import EnvironmentNotInstalledError

    monkeypatch.chdir(pixi_workspace)

    with pytest.raises(EnvironmentNotInstalledError):
        execute_list(make_args(_DEFAULTS))


def test_list_packages_undefined_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from conda_workspaces.exceptions import EnvironmentNotFoundError

    monkeypatch.chdir(pixi_workspace)

    with pytest.raises(EnvironmentNotFoundError):
        execute_list(make_args(_DEFAULTS,environment="nonexistent"))


@pytest.fixture
def _stub_prefix_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub PrefixData so _list_packages doesn't need real conda-meta."""
    from dataclasses import dataclass

    @dataclass
    class FakeRecord:
        name: str
        version: str
        build: str

    records = [
        FakeRecord("numpy", "1.26.4", "py312h1234abc_0"),
        FakeRecord("python", "3.12.3", "h5678def_0"),
    ]

    class FakePrefixData:
        def __init__(self, prefix: str) -> None:
            self._prefix = prefix

        def is_environment(self) -> bool:
            from pathlib import Path

            return (Path(self._prefix) / "conda-meta").is_dir()

        def iter_records(self):
            return iter(records)

    monkeypatch.setattr(
        "conda.core.envs_manager.PrefixData", FakePrefixData
    )


@pytest.mark.parametrize(
    "json_flag",
    [False, True],
    ids=["text", "json"],
)
def test_list_packages(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_workspace_env: CreateWorkspaceEnv,
    _stub_prefix_data: None,
    json_flag: bool,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    tmp_workspace_env(pixi_workspace, "default")

    args = make_args(_DEFAULTS,json=json_flag)
    result = execute_list(args)
    assert result == 0
    out = capsys.readouterr().out

    if json_flag:
        data = json.loads(out)
        names = {r["name"] for r in data}
        assert names == {"numpy", "python"}
        assert data[0]["version"] == "1.26.4"
    else:
        assert "numpy" in out
        assert "python" in out
        assert "1.26.4" in out


def test_list_packages_empty(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_workspace_env: CreateWorkspaceEnv,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    tmp_workspace_env(pixi_workspace, "default")

    class EmptyPrefixData:
        def __init__(self, prefix: str) -> None:
            self._prefix = prefix

        def is_environment(self) -> bool:
            from pathlib import Path

            return (Path(self._prefix) / "conda-meta").is_dir()

        def iter_records(self):
            return iter([])

    monkeypatch.setattr(
        "conda.core.envs_manager.PrefixData", EmptyPrefixData
    )

    args = make_args(_DEFAULTS)
    result = execute_list(args)
    assert result == 0
    assert "No packages installed" in capsys.readouterr().out
