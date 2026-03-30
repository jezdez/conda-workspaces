"""Tests for conda_workspaces.cli.workspace.lock."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from conda_workspaces.cli.workspace.lock import execute_lock
from conda_workspaces.exceptions import EnvironmentNotFoundError

from ..conftest import make_args

if TYPE_CHECKING:
    from pathlib import Path

_DEFAULTS = {
    "file": None,
    "environment": None,
}


@pytest.mark.parametrize(
    "env_arg, expected_keys, output_fragment",
    [
        ("default", {"default"}, "Updated"),
        (None, {"default", "test"}, "Updated"),
    ],
    ids=["single-env", "all-envs"],
)
def test_lock_envs(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    env_arg: str | None,
    expected_keys: set[str],
    output_fragment: str,
) -> None:
    monkeypatch.chdir(pixi_workspace)

    lock_calls: list[dict] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.workspace.lock.generate_lockfile",
        lambda ctx, resolved_envs: (
            lock_calls.append(resolved_envs),
            pixi_workspace / "conda.lock",
        )[1],
    )

    result = execute_lock(make_args(_DEFAULTS, environment=env_arg))
    assert result == 0
    assert len(lock_calls) == 1
    assert set(lock_calls[0].keys()) == expected_keys
    assert output_fragment in capsys.readouterr().out


def test_lock_unknown_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(pixi_workspace)

    with pytest.raises(EnvironmentNotFoundError):
        execute_lock(make_args(_DEFAULTS, environment="nonexistent"))
