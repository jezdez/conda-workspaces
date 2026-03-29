"""``conda workspace lock`` — solve and generate lockfiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console

from ...exceptions import EnvironmentNotFoundError
from ...lockfile import generate_lockfile, lockfile_path
from ...resolver import resolve_all_environments, resolve_environment
from .. import status
from . import workspace_context_from_args

if TYPE_CHECKING:
    import argparse


def execute_lock(args: argparse.Namespace, *, console: Console | None = None) -> int:
    """Solve workspace environments and write ``conda.lock``."""
    if console is None:
        console = Console(highlight=False)
    config, ctx = workspace_context_from_args(args)

    env_name = getattr(args, "environment", None)

    if env_name:
        if env_name not in config.environments:
            raise EnvironmentNotFoundError(env_name, list(config.environments.keys()))
        resolved = resolve_environment(config, env_name, ctx.platform)
        path = generate_lockfile(ctx, {env_name: resolved})
        status.done(console, env_name, detail=str(path))
    else:
        resolved_all = resolve_all_environments(config, ctx.platform)
        path = generate_lockfile(ctx, resolved_all)
        for name in resolved_all:
            status.done(console, name)
        n = len(resolved_all)
        console.print(
            f"{n}"
            f" {'environment' if n == 1 else 'environments'}"
            f" locked in"
            f" [dim]{lockfile_path(ctx)}[/dim]."
        )

    return 0
