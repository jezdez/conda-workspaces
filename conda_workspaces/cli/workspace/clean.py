"""``conda workspace clean`` — remove installed workspace environments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.exceptions import CondaSystemExit, DryRunExit
from conda.reporters import confirm_yn
from rich.console import Console

from ...envs import clean_all, list_installed_environments, remove_environment
from ...exceptions import EnvironmentNotFoundError
from .. import status
from . import workspace_context_from_args

if TYPE_CHECKING:
    import argparse


def execute_clean(args: argparse.Namespace, *, console: Console | None = None) -> int:
    """Remove installed workspace environments."""
    if console is None:
        console = Console(highlight=False)
    config, ctx = workspace_context_from_args(args)

    env_name = getattr(args, "environment", None)

    try:
        if env_name:
            if env_name not in config.environments:
                raise EnvironmentNotFoundError(
                    env_name, list(config.environments.keys())
                )

            if not ctx.env_exists(env_name):
                console.print(
                    f"Environment [bold]'{env_name}'[/bold] is not installed."
                )
                return 0

            confirm_yn(f"Remove environment '{env_name}'?")

            remove_environment(ctx, env_name)
            status.done(console, env_name)
        else:
            installed = list_installed_environments(ctx)
            if not installed:
                console.print("No environments installed.")
                return 0

            console.print(
                f"This will remove {len(installed)}"
                f" {'environment' if len(installed) == 1 else 'environments'}:"
            )
            for name in installed:
                console.print(f"  - {name}")
            confirm_yn("Continue?")

            clean_all(ctx)
            n = len(installed)
            console.print(
                f"{status.DONE} Removed {n}"
                f" {'environment' if n == 1 else 'environments'}."
            )
    except (CondaSystemExit, DryRunExit):
        return 0

    return 0
