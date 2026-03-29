"""Tests for conda_workspaces.cli.run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from conda.exceptions import ArgumentError

from conda_workspaces.cli.run import execute_run
from conda_workspaces.exceptions import (
    EnvironmentNotFoundError,
    EnvironmentNotInstalledError,
)

from .conftest import make_args

if TYPE_CHECKING:
    from pathlib import Path

    from tests.conftest import CreateWorkspaceEnv

_DEFAULTS = {"file": None, "environment": "default", "cmd": []}


@dataclass
class FakeResponse:
    """Stand-in for subprocess_call return value."""

    rc: int = 0
    stdout: str = ""
    stderr: str = ""


def _stub_run_deps(
    monkeypatch: pytest.MonkeyPatch,
    *,
    rc: int = 0,
    recorded_cmds: list | None = None,
) -> None:
    """Stub all conda imports used by execute_run for success paths."""
    if recorded_cmds is None:
        recorded_cmds = []

    class FakeContext:
        root_prefix = "/fake/root"

    monkeypatch.setattr("conda_workspaces.cli.run.conda_context", FakeContext())

    def fake_wrap(root_prefix, prefix, dev, debug, cmd):
        recorded_cmds.append(cmd)
        return "/tmp/fake_script.sh", ["bash", "/tmp/fake_script.sh"]

    monkeypatch.setattr("conda_workspaces.cli.run.wrap_subprocess_call", fake_wrap)

    def fake_subprocess_call(
        command, *, env=None, path=None, raise_on_error=False, capture_output=False
    ):
        return FakeResponse(rc=rc)

    monkeypatch.setattr(
        "conda_workspaces.cli.run.subprocess_call", fake_subprocess_call
    )
    monkeypatch.setattr("conda_workspaces.cli.run.encode_environment", lambda env: env)
    monkeypatch.setattr("conda_workspaces.cli.run.rm_rf", lambda path: None)


@pytest.mark.parametrize(
    "cmd, exc_type, match",
    [
        ([], ArgumentError, "No command"),
        (["echo", "hi"], EnvironmentNotInstalledError, "not installed"),
    ],
    ids=["no-command", "not-installed"],
)
def test_run_error(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    cmd: list[str],
    exc_type: type,
    match: str,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS,cmd=cmd)
    with pytest.raises(exc_type, match=match):
        execute_run(args)


def test_run_strips_double_dash(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_workspace_env: CreateWorkspaceEnv,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    tmp_workspace_env(pixi_workspace, "default")

    recorded_cmds: list[list[str]] = []
    _stub_run_deps(monkeypatch, recorded_cmds=recorded_cmds)

    args = make_args(_DEFAULTS,cmd=["--", "pytest", "-v"])
    execute_run(args)

    # wrap_subprocess_call should receive the cmd without leading "--"
    assert recorded_cmds[0] == ["pytest", "-v"]


@pytest.mark.parametrize(
    "rc, cmd",
    [
        (0, ["echo", "hello"]),
        (42, ["false"]),
    ],
    ids=["success", "nonzero-exit"],
)
def test_run_exit_code(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_workspace_env: CreateWorkspaceEnv,
    rc: int,
    cmd: list[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    tmp_workspace_env(pixi_workspace, "default")

    _stub_run_deps(monkeypatch, rc=rc)

    args = make_args(_DEFAULTS,cmd=cmd)
    result = execute_run(args)
    assert result == rc


def test_run_undefined_environment(
    pixi_workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Undefined env raises EnvironmentNotFoundError."""
    monkeypatch.chdir(pixi_workspace)
    args = make_args(_DEFAULTS,environment="nonexistent", cmd=["echo", "hi"])
    with pytest.raises(EnvironmentNotFoundError, match="not defined"):
        execute_run(args)
