"""Tests for conda_workspaces.envs."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from conda_workspaces.context import WorkspaceContext
from conda_workspaces.envs import (
    clean_all,
    get_environment_info,
    install_environment,
    list_installed_environments,
    remove_environment,
)
from conda_workspaces.exceptions import SolveError
from conda_workspaces.models import (
    Channel,
    Environment,
    Feature,
    MatchSpec,
    WorkspaceConfig,
)


@pytest.fixture
def workspace(tmp_path: Path) -> WorkspaceContext:
    """A WorkspaceContext backed by tmp_path with a simple config."""
    config = WorkspaceConfig(
        name="envs-test",
        root=str(tmp_path),
        channels=[Channel("conda-forge")],
        platforms=["linux-64"],
        features={
            "default": Feature(
                name="default",
                conda_dependencies={"python": MatchSpec("python >=3.10")},
            ),
        },
        environments={"default": Environment(name="default")},
    )
    return WorkspaceContext(config)


def _make_fake_env(
    ctx: WorkspaceContext, name: str, pkg_count: int = 0
) -> Path:
    """Create a fake installed environment with optional package jsons."""
    prefix = ctx.env_prefix(name)
    meta = prefix / "conda-meta"
    meta.mkdir(parents=True)
    (meta / "history").write_text("", encoding="utf-8")
    for i in range(pkg_count):
        content = json.dumps({"name": f"pkg-{i}"})
        (meta / f"pkg-{i}.json").write_text(content, encoding="utf-8")
    return prefix


def test_remove_environment(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_fake_env(workspace, "default")
    assert workspace.env_exists("default")

    monkeypatch.setattr("conda_workspaces.envs.unregister_env", lambda path: None)
    remove_environment(workspace, "default")
    assert not workspace.env_exists("default")


def test_remove_environment_nonexistent(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Removing a non-existent env is a no-op (no error)."""
    monkeypatch.setattr("conda_workspaces.envs.unregister_env", lambda path: None)
    remove_environment(workspace, "nonexistent")


def test_clean_all(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_fake_env(workspace, "default")
    _make_fake_env(workspace, "test")
    assert workspace.envs_dir.is_dir()

    monkeypatch.setattr("conda_workspaces.envs.unregister_env", lambda path: None)
    clean_all(workspace)
    assert not workspace.envs_dir.is_dir()


def test_clean_all_no_envs_dir(workspace: WorkspaceContext) -> None:
    """clean_all is a no-op when envs_dir doesn't exist."""
    clean_all(workspace)  # should not raise


@pytest.mark.parametrize(
    "env_names, expected",
    [
        ([], []),
        (["default"], ["default"]),
        (["test", "default", "docs"], ["default", "docs", "test"]),
    ],
    ids=["empty", "single", "sorted-multiple"],
)
def test_list_installed_environments(
    workspace: WorkspaceContext, env_names: list[str], expected: list[str]
) -> None:
    for name in env_names:
        _make_fake_env(workspace, name)
    assert list_installed_environments(workspace) == expected


def test_list_installed_ignores_non_conda_dirs(workspace: WorkspaceContext) -> None:
    """Directories without conda-meta should be excluded."""
    _make_fake_env(workspace, "real")
    (workspace.envs_dir / "not-an-env").mkdir(parents=True)
    assert list_installed_environments(workspace) == ["real"]


def test_list_installed_no_envs_dir(workspace: WorkspaceContext) -> None:
    assert list_installed_environments(workspace) == []


@pytest.mark.parametrize(
    "installed, pkg_count, expect_packages",
    [
        (False, 0, False),
        (True, 0, True),
        (True, 5, True),
    ],
    ids=["not-installed", "installed-empty", "installed-with-pkgs"],
)
def test_get_environment_info(
    workspace: WorkspaceContext,
    installed: bool,
    pkg_count: int,
    expect_packages: bool,
) -> None:
    if installed:
        _make_fake_env(workspace, "default", pkg_count=pkg_count)

    info = get_environment_info(workspace, "default")
    assert info["name"] == "default"
    assert info["exists"] is installed

    if expect_packages:
        assert info["packages"] == pkg_count
    else:
        assert "packages" not in info


@dataclass
class FakeTransaction:
    """Stand-in for UnlinkLinkTransaction."""

    nothing_to_do: bool = False
    summary_printed: bool = field(default=False, init=False)
    downloaded: bool = field(default=False, init=False)
    executed: bool = field(default=False, init=False)

    def print_transaction_summary(self) -> None:
        self.summary_printed = True

    def download_and_extract(self) -> None:
        self.downloaded = True

    def execute(self) -> None:
        self.executed = True


@dataclass
class FakeSolver:
    """Stand-in for the solver backend."""

    prefix: str = ""
    channels: list = field(default_factory=list)
    subdirs: tuple = ()
    specs_to_add: list = field(default_factory=list)
    txn: FakeTransaction = field(default_factory=FakeTransaction)

    def solve_for_transaction(self, **kwargs) -> FakeTransaction:
        return self.txn


def _stub_conda_imports(monkeypatch: pytest.MonkeyPatch, solver: FakeSolver) -> None:
    """Patch all conda imports inside install_environment."""
    import conda_workspaces.envs as envs_mod

    # Fake plugin manager
    class FakePluginManager:
        def get_cached_solver_backend(self):
            def factory(prefix, channels, subdirs, specs_to_add=(), **kw):
                solver.prefix = prefix
                solver.channels = channels
                solver.subdirs = subdirs
                solver.specs_to_add = list(specs_to_add)
                return solver
            return factory

    class FakeContext:
        plugin_manager = FakePluginManager()
        subdirs = ("linux-64", "noarch")

    monkeypatch.setattr(envs_mod, "conda_context", FakeContext())


def test_install_empty_specs(workspace: WorkspaceContext) -> None:
    """With no dependencies, install just creates the prefix dir."""
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(name="default")
    install_environment(workspace, resolved)
    assert workspace.env_prefix("default").is_dir()


@pytest.mark.parametrize(
    "nothing_to_do, dry_run, expect_summary, expect_downloaded, expect_executed",
    [
        (False, False, False, True, True),
        (False, True, True, False, False),
        (True, False, False, False, False),
    ],
    ids=["new-env", "dry-run", "nothing-to-do"],
)
def test_install_transaction_outcomes(
    workspace: WorkspaceContext,
    monkeypatch: pytest.MonkeyPatch,
    nothing_to_do: bool,
    dry_run: bool,
    expect_summary: bool,
    expect_downloaded: bool,
    expect_executed: bool,
) -> None:
    from conda_workspaces.resolver import ResolvedEnvironment

    txn = FakeTransaction(nothing_to_do=nothing_to_do)
    solver = FakeSolver(txn=txn)
    _stub_conda_imports(monkeypatch, solver)

    resolved = ResolvedEnvironment(
        name="default",
        conda_dependencies={"python": MatchSpec("python >=3.10")},
        channels=[Channel("conda-forge")],
    )
    install_environment(workspace, resolved, dry_run=dry_run)

    assert txn.summary_printed is expect_summary
    assert txn.downloaded is expect_downloaded
    assert txn.executed is expect_executed


def test_install_force_reinstall(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    from conda_workspaces.resolver import ResolvedEnvironment

    # Create a pre-existing environment
    _make_fake_env(workspace, "default")
    assert workspace.env_exists("default")

    txn = FakeTransaction()
    solver = FakeSolver(txn=txn)
    _stub_conda_imports(monkeypatch, solver)

    resolved = ResolvedEnvironment(
        name="default",
        conda_dependencies={"python": MatchSpec("python >=3.10")},
        channels=[Channel("conda-forge")],
    )
    install_environment(workspace, resolved, force_reinstall=True)

    # Old env was removed and new one was installed
    assert txn.downloaded
    assert txn.executed


def test_install_existing_env_uses_freeze(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Updating an existing env passes UpdateModifier.FREEZE_INSTALLED."""
    from conda_workspaces.resolver import ResolvedEnvironment

    _make_fake_env(workspace, "default")

    recorded_kwargs: dict = {}

    class RecordingSolver:
        def __init__(self, prefix, channels, subdirs, specs_to_add=(), **kw):
            pass

        def solve_for_transaction(self, **kwargs):
            recorded_kwargs.update(kwargs)
            return FakeTransaction()

    import conda_workspaces.envs as envs_mod

    class FakePluginManager:
        def get_cached_solver_backend(self):
            return RecordingSolver

    class FakeContext:
        plugin_manager = FakePluginManager()
        subdirs = ("linux-64", "noarch")

    monkeypatch.setattr(envs_mod, "conda_context", FakeContext())

    resolved = ResolvedEnvironment(
        name="default",
        conda_dependencies={"python": MatchSpec("python >=3.10")},
        channels=[Channel("conda-forge")],
    )
    install_environment(workspace, resolved)

    from conda.base.constants import UpdateModifier
    assert recorded_kwargs.get("update_modifier") is UpdateModifier.FREEZE_INSTALLED


def test_install_solve_error(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    from conda.exceptions import UnsatisfiableError

    from conda_workspaces.resolver import ResolvedEnvironment

    class FailingSolver:
        def __init__(self, prefix, channels, subdirs, specs_to_add=(), **kw):
            pass

        def solve_for_transaction(self, **kwargs):
            raise UnsatisfiableError({})

    import conda_workspaces.envs as envs_mod

    class FakePluginManager:
        def get_cached_solver_backend(self):
            return FailingSolver

    class FakeContext:
        plugin_manager = FakePluginManager()
        subdirs = ("linux-64", "noarch")

    monkeypatch.setattr(envs_mod, "conda_context", FakeContext())

    resolved = ResolvedEnvironment(
        name="default",
        conda_dependencies={"python": MatchSpec("python >=3.10")},
        channels=[Channel("conda-forge")],
    )
    with pytest.raises(SolveError, match="default"):
        install_environment(workspace, resolved)


def test_install_no_solver_backend(
    workspace: WorkspaceContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    import conda_workspaces.envs as envs_mod
    from conda_workspaces.resolver import ResolvedEnvironment

    class FakePluginManager:
        def get_cached_solver_backend(self):
            return None

    class FakeContext:
        plugin_manager = FakePluginManager()
        subdirs = ("linux-64", "noarch")

    monkeypatch.setattr(envs_mod, "conda_context", FakeContext())

    resolved = ResolvedEnvironment(
        name="default",
        conda_dependencies={"python": MatchSpec("python >=3.10")},
        channels=[Channel("conda-forge")],
    )
    with pytest.raises(SolveError, match="No solver backend"):
        install_environment(workspace, resolved)


def test_install_pypi_deps_no_conda_pypi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When conda-pypi is not installed, warns and returns."""
    import builtins
    import logging

    from conda_workspaces.envs import _install_pypi_deps
    from conda_workspaces.models import PyPIDependency
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(
        name="default",
        pypi_dependencies={
            "requests": PyPIDependency(name="requests"),
        },
    )

    real_import = builtins.__import__

    def _block_conda_pypi(name, *args, **kwargs):
        if name.startswith("conda_pypi"):
            raise ImportError("no conda-pypi")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_conda_pypi)

    with caplog.at_level(logging.WARNING):
        _install_pypi_deps(tmp_path, resolved)

    assert "conda-pypi is not installed" in caplog.text
    assert "requests" in caplog.text


def test_install_pypi_deps_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When conda-pypi is available, calls ConvertTree + run_conda_install."""
    import sys
    import types

    from conda_workspaces.envs import _install_pypi_deps
    from conda_workspaces.models import PyPIDependency
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(
        name="default",
        pypi_dependencies={
            "requests": PyPIDependency(name="requests", spec=">=2.28"),
        },
    )

    convert_calls: list[list] = []
    install_calls: list[dict] = []

    def fake_convert_tree_factory(prefix):
        repo = tmp_path / "conda-pypi-repo"
        repo.mkdir(exist_ok=True)

        class _ct:
            pass

        ct = _ct()
        ct.repo = repo

        def convert(specs):
            convert_calls.append(specs)

        ct.convert_tree = convert
        return ct

    def fake_run_conda_install(prefix, specs, **kwargs):
        install_calls.append({"prefix": prefix, "specs": specs, **kwargs})
        return 0

    # Wire up fake conda_pypi modules via sys.modules
    conda_pypi = types.ModuleType("conda_pypi")
    ct_mod = types.ModuleType("conda_pypi.convert_tree")
    ct_mod.ConvertTree = fake_convert_tree_factory
    main_mod = types.ModuleType("conda_pypi.main")
    main_mod.run_conda_install = fake_run_conda_install
    tr_mod = types.ModuleType("conda_pypi.translate")
    tr_mod.pypi_to_conda_name = lambda n: n.replace("-", "_")

    monkeypatch.setitem(sys.modules, "conda_pypi", conda_pypi)
    monkeypatch.setitem(sys.modules, "conda_pypi.convert_tree", ct_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.main", main_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.translate", tr_mod)

    _install_pypi_deps(tmp_path, resolved)

    assert len(convert_calls) == 1
    assert len(install_calls) == 1
    assert install_calls[0]["yes"] is True
    assert install_calls[0]["quiet"] is True


def test_install_pypi_deps_exception_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When convert_tree raises, logs warning and continues."""
    import logging
    import sys
    import types

    from conda_workspaces.envs import _install_pypi_deps
    from conda_workspaces.models import PyPIDependency
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(
        name="default",
        pypi_dependencies={"flask": PyPIDependency(name="flask")},
    )

    def broken_factory(prefix):
        repo = tmp_path / "repo"
        repo.mkdir(exist_ok=True)

        class _ct:
            pass

        ct = _ct()
        ct.repo = repo

        def convert(specs):
            raise RuntimeError("download failed")

        ct.convert_tree = convert
        return ct

    conda_pypi = types.ModuleType("conda_pypi")
    ct_mod = types.ModuleType("conda_pypi.convert_tree")
    ct_mod.ConvertTree = broken_factory
    main_mod = types.ModuleType("conda_pypi.main")
    main_mod.run_conda_install = lambda *a, **kw: 0
    tr_mod = types.ModuleType("conda_pypi.translate")
    tr_mod.pypi_to_conda_name = lambda n: n

    monkeypatch.setitem(sys.modules, "conda_pypi", conda_pypi)
    monkeypatch.setitem(sys.modules, "conda_pypi.convert_tree", ct_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.main", main_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.translate", tr_mod)

    with caplog.at_level(logging.WARNING):
        _install_pypi_deps(tmp_path, resolved)

    assert "Failed to install PyPI dependencies" in caplog.text
    assert "flask" in caplog.text
