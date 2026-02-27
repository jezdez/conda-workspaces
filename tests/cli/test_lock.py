"""Tests for conda_workspaces.cli.lock."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import pytest

from conda_workspaces.cli.lock import execute_lock

if TYPE_CHECKING:
    from pathlib import Path

_LOCK_DEFAULTS = {
    "file": None,
    "environment": None,
}


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**{**_LOCK_DEFAULTS, **kwargs})


def test_lock_single_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)

    monkeypatch.setattr(
        "conda_workspaces.cli.lock.WorkspaceContext.env_exists",
        lambda self, name: True,
    )

    lock_calls: list[list[str] | None] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.lock.generate_lockfile",
        lambda ctx, env_names=None: (
            lock_calls.append(env_names),
            pixi_workspace / "conda.lock",
        )[1],
    )

    result = execute_lock(_make_args(environment="default"))
    assert result == 0
    assert lock_calls == [["default"]]
    assert "Lockfile written to" in capsys.readouterr().out


def test_lock_single_env_not_installed(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(pixi_workspace)

    monkeypatch.setattr(
        "conda_workspaces.cli.lock.WorkspaceContext.env_exists",
        lambda self, name: False,
    )

    from conda_workspaces.exceptions import EnvironmentNotInstalledError

    with pytest.raises(EnvironmentNotInstalledError):
        execute_lock(_make_args(environment="default"))


def test_lock_all_envs(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)

    # Only "default" is installed, "test" is not
    monkeypatch.setattr(
        "conda_workspaces.cli.lock.WorkspaceContext.env_exists",
        lambda self, name: name == "default",
    )

    lock_calls: list[list[str] | None] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.lock.generate_lockfile",
        lambda ctx, env_names=None: (
            lock_calls.append(env_names),
            pixi_workspace / "conda.lock",
        )[1],
    )

    result = execute_lock(_make_args())
    assert result == 0
    assert lock_calls == [["default"]]
    out = capsys.readouterr().out
    assert "default" in out
    assert "skipped" in out
    assert "1 environment(s) locked" in out


def test_lock_all_envs_all_installed(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)

    monkeypatch.setattr(
        "conda_workspaces.cli.lock.WorkspaceContext.env_exists",
        lambda self, name: True,
    )

    lock_calls: list[list[str] | None] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.lock.generate_lockfile",
        lambda ctx, env_names=None: (
            lock_calls.append(env_names),
            pixi_workspace / "conda.lock",
        )[1],
    )

    result = execute_lock(_make_args())
    assert result == 0
    assert len(lock_calls) == 1
    assert set(lock_calls[0]) == {"default", "test"}
    assert "2 environment(s) locked" in capsys.readouterr().out
