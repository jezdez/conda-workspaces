"""Tests for conda_workspaces.cli.install."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

import pytest

from conda_workspaces.cli.install import execute_install

if TYPE_CHECKING:
    from pathlib import Path

_INSTALL_DEFAULTS = {
    "file": None,
    "environment": None,
    "force_reinstall": False,
    "dry_run": False,
    "locked": False,
}


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**{**_INSTALL_DEFAULTS, **kwargs})


def _stub_lockfile(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub generate_lockfile to a no-op for tests that don't care about it."""
    monkeypatch.setattr(
        "conda_workspaces.cli.install.generate_lockfile",
        lambda ctx, env_names=None: None,
    )


def test_install_single_env(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    _stub_lockfile(monkeypatch)

    # Stub install_environment to record calls without actually solving
    calls: list[tuple[str, bool, bool]] = []

    def fake_install(ctx, resolved, *, force_reinstall=False, dry_run=False):
        calls.append((resolved.name, force_reinstall, dry_run))

    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_environment", fake_install
    )

    args = _make_args(environment="default")
    result = execute_install(args)
    assert result == 0
    assert len(calls) == 1
    assert calls[0][0] == "default"
    assert "Installing" in capsys.readouterr().out


def test_install_all_envs(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)
    _stub_lockfile(monkeypatch)

    calls: list[str] = []

    def fake_install(ctx, resolved, *, force_reinstall=False, dry_run=False):
        calls.append(resolved.name)

    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_environment", fake_install
    )

    args = _make_args()
    result = execute_install(args)
    assert result == 0
    assert set(calls) == {"default", "test"}
    assert "2 environment(s)" in capsys.readouterr().out


@pytest.mark.parametrize(
    "force, dry_run",
    [
        (True, False),
        (False, True),
        (True, True),
    ],
    ids=["force", "dry-run", "force-dry-run"],
)
def test_install_flags_forwarded(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    force: bool,
    dry_run: bool,
) -> None:
    monkeypatch.chdir(pixi_workspace)
    _stub_lockfile(monkeypatch)

    recorded: list[tuple[bool, bool]] = []

    def fake_install(ctx, resolved, *, force_reinstall=False, dry_run=False):
        recorded.append((force_reinstall, dry_run))

    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_environment", fake_install
    )

    args = _make_args(environment="default", force_reinstall=force, dry_run=dry_run)
    execute_install(args)
    assert recorded[0] == (force, dry_run)


def test_install_generates_lockfile(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(pixi_workspace)

    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_environment",
        lambda ctx, resolved, **kw: None,
    )

    lock_calls: list[list[str] | None] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.install.generate_lockfile",
        lambda ctx, env_names=None: lock_calls.append(env_names),
    )

    args = _make_args(environment="default")
    execute_install(args)
    assert lock_calls == [["default"]]


def test_install_all_generates_lockfile(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(pixi_workspace)

    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_environment",
        lambda ctx, resolved, **kw: None,
    )

    lock_calls: list[list[str] | None] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.install.generate_lockfile",
        lambda ctx, env_names=None: lock_calls.append(env_names),
    )

    args = _make_args()
    execute_install(args)
    # Should be called once with all env names
    assert len(lock_calls) == 1
    assert set(lock_calls[0]) == {"default", "test"}


def test_install_dry_run_skips_lockfile(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(pixi_workspace)

    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_environment",
        lambda ctx, resolved, **kw: None,
    )

    lock_calls: list[list[str] | None] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.install.generate_lockfile",
        lambda ctx, env_names=None: lock_calls.append(env_names),
    )

    args = _make_args(environment="default", dry_run=True)
    execute_install(args)
    assert lock_calls == []


def test_install_locked_single(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)

    locked_calls: list[str] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_from_lockfile",
        lambda ctx, name: locked_calls.append(name),
    )

    args = _make_args(environment="default", locked=True)
    result = execute_install(args)
    assert result == 0
    assert locked_calls == ["default"]
    assert "from lockfile" in capsys.readouterr().out


def test_install_locked_all(
    pixi_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(pixi_workspace)

    locked_calls: list[str] = []
    monkeypatch.setattr(
        "conda_workspaces.cli.install.install_from_lockfile",
        lambda ctx, name: locked_calls.append(name),
    )

    args = _make_args(locked=True)
    result = execute_install(args)
    assert result == 0
    assert set(locked_calls) == {"default", "test"}
    assert "from lockfiles" in capsys.readouterr().out
