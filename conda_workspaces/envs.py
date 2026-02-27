"""Environment manager — create, update, and remove project-local envs.

Uses conda's Solver API to install packages into project-scoped
environments under ``.conda/envs/<name>/``.  Each environment is
a standard conda prefix that can be activated with ``conda activate``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.base.constants import UpdateModifier
from conda.base.context import context as conda_context
from conda.core.envs_manager import PrefixData, unregister_env
from conda.exceptions import UnsatisfiableError
from conda.gateways.disk.delete import rm_rf
from conda.models.match_spec import MatchSpec

from .exceptions import SolveError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from .context import WorkspaceContext
    from .resolver import ResolvedEnvironment


def _iter_installed_prefixes(envs_dir: Path) -> Iterator[Path]:
    """Yield paths of valid conda environments under *envs_dir*."""
    if not envs_dir.is_dir():
        return
    for d in envs_dir.iterdir():
        if d.is_dir() and PrefixData(str(d)).is_environment():
            yield d


def install_environment(
    ctx: WorkspaceContext,
    resolved: ResolvedEnvironment,
    *,
    force_reinstall: bool = False,
    dry_run: bool = False,
) -> None:
    """Create or update a project-local environment.

    Uses conda's Solver API directly instead of shelling out, which
    avoids the overhead of a subprocess and gives full control over
    the solve/install transaction.

    Raises ``SolveError`` if dependency resolution fails.
    """
    prefix = ctx.env_prefix(resolved.name)
    exists = ctx.env_exists(resolved.name)

    if exists and force_reinstall:
        rm_rf(prefix)
        exists = False

    # Build the spec list from resolved dependencies
    specs = [
        MatchSpec(dep.conda_build_form())
        for dep in resolved.conda_dependencies.values()
    ]
    if not specs:
        # Nothing to install — just ensure the prefix directory exists
        prefix.mkdir(parents=True, exist_ok=True)
        return

    # Get the solver backend (respects solver plugins)
    solver_backend = conda_context.plugin_manager.get_cached_solver_backend()
    if solver_backend is None:
        raise SolveError(resolved.name, "No solver backend found")

    channels = list(resolved.channels)
    subdirs = conda_context.subdirs

    solver = solver_backend(
        str(prefix),
        channels,
        subdirs,
        specs_to_add=specs,
    )

    try:
        if exists:
            txn = solver.solve_for_transaction(
                update_modifier=UpdateModifier.FREEZE_INSTALLED,
            )
        else:
            txn = solver.solve_for_transaction()
    except (UnsatisfiableError, SystemExit) as exc:
        raise SolveError(resolved.name, str(exc)) from exc

    if txn.nothing_to_do:
        return

    if dry_run:
        txn.print_transaction_summary()
        return

    txn.download_and_extract()
    txn.execute()

    # Install PyPI dependencies via conda-pypi (if available)
    if resolved.pypi_dependencies and not dry_run:
        _install_pypi_deps(prefix, resolved)


def _install_pypi_deps(prefix: Path, resolved: ResolvedEnvironment) -> None:
    """Install PyPI dependencies into an environment via conda-pypi.

    Uses conda-pypi's ``ConvertTree`` to download wheels from PyPI,
    convert them to ``.conda`` packages in a local channel, and then
    installs them with ``conda install``.  This means PyPI deps end up
    as real conda packages in the prefix — no pip shim required.

    If ``conda-pypi`` is not installed, emits a warning listing the
    uninstalled PyPI dependencies and returns without error.
    """
    import logging

    log = logging.getLogger(__name__)
    pypi_specs = [str(dep) for dep in resolved.pypi_dependencies.values()]

    try:
        from conda_pypi.convert_tree import ConvertTree  # type: ignore[import-untyped]
        from conda_pypi.main import run_conda_install  # type: ignore[import-untyped]
        from conda_pypi.translate import (
            pypi_to_conda_name,  # type: ignore[import-untyped]
        )
    except ImportError:
        log.warning(
            "PyPI dependencies found but conda-pypi is not installed.\n"
            "  Skipped PyPI packages: %s\n"
            "  Install conda-pypi to enable: conda install conda-pypi",
            ", ".join(pypi_specs),
        )
        return

    log.info("Installing %d PyPI package(s) via conda-pypi...", len(pypi_specs))
    try:
        # Translate PyPI names to conda names and build MatchSpec objects
        match_specs = []
        for dep in resolved.pypi_dependencies.values():
            conda_name = pypi_to_conda_name(dep.name)
            spec_str = f"{conda_name}{dep.spec}" if dep.spec else conda_name
            match_specs.append(MatchSpec(spec_str))

        # Convert wheels to conda packages in a local channel
        converter = ConvertTree(prefix)
        channel_url = converter.repo.as_uri()
        converter.convert_tree(match_specs)

        # Install via conda so they become real conda packages
        run_conda_install(
            prefix,
            match_specs,
            channels=[channel_url],
            yes=True,
            quiet=True,
        )
    except Exception as exc:
        log.warning(
            "Failed to install PyPI dependencies via conda-pypi: %s\n  Skipped: %s",
            exc,
            ", ".join(pypi_specs),
        )


def remove_environment(ctx: WorkspaceContext, env_name: str) -> None:
    """Remove a project-local environment by deleting its prefix."""
    prefix = ctx.env_prefix(env_name)
    if prefix.is_dir():
        unregister_env(str(prefix))
        rm_rf(prefix)


def clean_all(ctx: WorkspaceContext) -> None:
    """Remove all project-local environments."""
    envs_dir = ctx.envs_dir
    for d in _iter_installed_prefixes(envs_dir):
        unregister_env(str(d))
    if envs_dir.is_dir():
        rm_rf(envs_dir)


def list_installed_environments(ctx: WorkspaceContext) -> list[str]:
    """Return names of environments that are currently installed."""
    return sorted(d.name for d in _iter_installed_prefixes(ctx.envs_dir))


def get_environment_info(
    ctx: WorkspaceContext, env_name: str
) -> dict[str, str | int | bool]:
    """Return basic info about an installed environment."""
    prefix = ctx.env_prefix(env_name)
    exists = ctx.env_exists(env_name)
    info: dict[str, str | int | bool] = {
        "name": env_name,
        "prefix": str(prefix),
        "exists": exists,
    }
    if exists:
        # Count installed packages via conda-meta
        meta_dir = prefix / "conda-meta"
        pkg_count = sum(1 for f in meta_dir.glob("*.json") if f.name != "history")
        info["packages"] = pkg_count
    return info
