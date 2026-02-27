"""Tests for conda_workspaces.cli.list."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from conda_workspaces.cli.list import execute_list

_LIST_DEFAULTS = {"file": None, "installed": False, "json": False}


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**{**_LIST_DEFAULTS, **kwargs})


def test_list_all_environments(
    pixi_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = _make_args()
    result = execute_list(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "default" in out
    assert "test" in out


def test_list_installed_only(
    pixi_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(pixi_workspace)
    # No environments installed yet
    args = _make_args(installed=True)
    result = execute_list(args)
    assert result == 0
    out = capsys.readouterr().out
    assert "No environments found" in out


def test_list_installed_with_env(
    pixi_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(pixi_workspace)
    # Fake-install the default env
    meta = pixi_workspace / ".conda" / "envs" / "default" / "conda-meta"
    meta.mkdir(parents=True)
    (meta / "history").write_text("", encoding="utf-8")

    args = _make_args(installed=True)
    execute_list(args)
    out = capsys.readouterr().out
    assert "default" in out
    # test env is not installed, should be filtered out
    assert "test" not in out


def test_list_json_output(
    pixi_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = _make_args(json=True)
    execute_list(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    names = {row["name"] for row in data}
    assert "default" in names
    assert "test" in names
