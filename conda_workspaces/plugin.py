"""Conda plugin registration for conda-workspaces.

This module is imported on *every* conda invocation via the entry point
system.  Only ``hookimpl`` and type imports are used at module level —
everything else is lazily imported inside the hooks to keep the
overhead under 1 ms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.plugins import hookimpl
from conda.plugins.types import (
    CondaEnvironmentExporter,
    CondaEnvironmentSpecifier,
    CondaSubcommand,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


@hookimpl
def conda_subcommands() -> Iterable[CondaSubcommand]:
    from .cli import configure_parser, execute

    yield CondaSubcommand(
        name="workspace",
        summary="Manage project-scoped multi-environment workspaces.",
        action=execute,  # ty: ignore[invalid-argument-type]
        configure_parser=configure_parser,
    )


@hookimpl
def conda_environment_specifiers() -> Iterable[CondaEnvironmentSpecifier]:
    """Register environment specifiers for workspace manifests and lockfiles.

    Allows ``conda env create --file conda.toml`` and
    ``conda env create --file conda.lock`` to work out of the box.
    """
    from .env_spec import CondaLockSpec, CondaWorkspaceSpec

    yield CondaEnvironmentSpecifier(
        name="conda-workspaces",
        environment_spec=CondaWorkspaceSpec,
    )
    yield CondaEnvironmentSpecifier(
        name="conda-workspaces-lock",
        environment_spec=CondaLockSpec,
    )


@hookimpl
def conda_environment_exporters() -> Iterable[CondaEnvironmentExporter]:
    """Register an environment exporter for ``conda.lock``.

    Allows ``conda export --format=conda-workspaces-lock --file=conda.lock``.
    """
    from .env_export import ALIASES, DEFAULT_FILENAMES, FORMAT, multiplatform_export

    yield CondaEnvironmentExporter(
        name=FORMAT,
        aliases=ALIASES,
        default_filenames=DEFAULT_FILENAMES,
        multiplatform_export=multiplatform_export,
    )
