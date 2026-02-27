"""``conda workspace lock`` — generate lockfiles for workspace environments."""

from __future__ import annotations

import argparse

from ..context import WorkspaceContext
from ..lockfile import generate_lockfile, lockfile_path
from ..parsers import detect_and_parse
from ..resolver import resolve_all_environments


def execute_lock(args: argparse.Namespace) -> int:
    """Generate a ``conda.lock`` for installed workspace environments."""
    manifest_path = getattr(args, "file", None)
    _, config = detect_and_parse(manifest_path)
    ctx = WorkspaceContext(config)

    env_name = getattr(args, "environment", None)

    if env_name:
        if not ctx.env_exists(env_name):
            from ..exceptions import EnvironmentNotInstalledError

            raise EnvironmentNotInstalledError(env_name)
        path = generate_lockfile(ctx, env_names=[env_name])
        print(f"Lockfile written to {path}")
    else:
        resolved_all = resolve_all_environments(config, ctx.platform)
        installed = [
            name for name in resolved_all if ctx.env_exists(name)
        ]
        skipped = [
            name for name in resolved_all if not ctx.env_exists(name)
        ]
        if installed:
            path = generate_lockfile(ctx, env_names=installed)
            for name in installed:
                print(f"  {name} -> {path}")
        for name in skipped:
            print(f"  {name} — skipped (not installed)")
        print(f"\n{len(installed)} environment(s) locked in {lockfile_path(ctx)}.")

    return 0
