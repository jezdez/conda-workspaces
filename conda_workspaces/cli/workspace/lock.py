"""``conda workspace lock`` — solve and generate lockfiles."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...exceptions import EnvironmentNotFoundError
from ...lockfile import generate_lockfile, lockfile_path
from ...resolver import resolve_all_environments, resolve_environment
from ._common import workspace_context_from_args

if TYPE_CHECKING:
    import argparse


def execute_lock(args: argparse.Namespace) -> int:
    """Solve workspace environments and write ``conda.lock``."""
    config, ctx = workspace_context_from_args(args)

    env_name = getattr(args, "environment", None)

    if env_name:
        if env_name not in config.environments:
            raise EnvironmentNotFoundError(
                env_name, list(config.environments.keys())
            )
        resolved = resolve_environment(config, env_name, ctx.platform)
        path = generate_lockfile(ctx, {env_name: resolved})
        print(f"Lockfile written to {path}")
    else:
        resolved_all = resolve_all_environments(config, ctx.platform)
        path = generate_lockfile(ctx, resolved_all)
        for name in resolved_all:
            print(f"  {name} -> {path}")
        print(f"\n{len(resolved_all)} environment(s) locked in {lockfile_path(ctx)}.")

    return 0
