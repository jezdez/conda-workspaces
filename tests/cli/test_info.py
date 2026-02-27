"""Tests for conda_workspaces.cli.info."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING

import pytest

from conda_workspaces.cli.info import execute_info

if TYPE_CHECKING:
    from pathlib import Path

_INFO_DEFAULTS = {"file": None, "env_name": "default", "json": False}


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**{**_INFO_DEFAULTS, **kwargs})


@pytest.mark.parametrize(
    "env_name, expected_fragments",
    [
        ("default", ["Environment: default", "Installed:   no", "conda-forge"]),
        ("test", ["Environment: test"]),
    ],
    ids=["default-text", "named-env"],
)
def test_info_text_output(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    env_name: str,
    expected_fragments: list[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = _make_args(env_name=env_name)
    result = execute_info(args)
    assert result == 0
    out = capsys.readouterr().out
    for fragment in expected_fragments:
        assert fragment in out


def test_info_installed_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    # Fake-install the default env with 3 packages
    meta = pixi_workspace / ".conda" / "envs" / "default" / "conda-meta"
    meta.mkdir(parents=True)
    (meta / "history").write_text("", encoding="utf-8")
    for i in range(3):
        (meta / f"pkg-{i}.json").write_text("{}", encoding="utf-8")

    args = _make_args()
    execute_info(args)
    out = capsys.readouterr().out
    assert "Installed:   yes" in out
    assert "Packages:    3" in out


@pytest.mark.parametrize(
    "env_name, expected_deps",
    [
        ("default", ["python"]),
        ("test", ["python", "pytest"]),
    ],
    ids=["default-deps", "test-deps"],
)
def test_info_shows_dependencies(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    env_name: str,
    expected_deps: list[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = _make_args(env_name=env_name)
    execute_info(args)
    out = capsys.readouterr().out
    for dep in expected_deps:
        assert dep in out


def test_info_json_output(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = _make_args(json=True)
    execute_info(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["name"] == "default"
    assert "conda_dependencies" in data
    assert "channels" in data
