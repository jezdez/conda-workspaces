"""``conda workspace install`` — create or update workspace environments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..context import WorkspaceContext
from ..envs import install_environment
from ..lockfile import generate_lockfile, install_from_lockfile
from ..parsers import detect_and_parse
from ..resolver import resolve_all_environments, resolve_environment

if TYPE_CHECKING:
    import argparse


def execute_install(args: argparse.Namespace) -> int:
    """Install (create/update) workspace environments."""
    manifest_path = getattr(args, "file", None)
    _, config = detect_and_parse(manifest_path)
    ctx = WorkspaceContext(config)

    env_name = getattr(args, "environment", None)
    force = getattr(args, "force_reinstall", False)
    dry_run = getattr(args, "dry_run", False)
    locked = getattr(args, "locked", False)

    if locked:
        return _install_locked(ctx, config, env_name)

    if env_name:
        resolved = resolve_environment(config, env_name, ctx.platform)
        print(f"Installing environment '{env_name}'...")
        install_environment(ctx, resolved, force_reinstall=force, dry_run=dry_run)
        if not dry_run:
            generate_lockfile(ctx, env_names=[env_name])
        print(f"Environment '{env_name}' is ready at {ctx.env_prefix(env_name)}")
    else:
        resolved_all = resolve_all_environments(config, ctx.platform)
        installed_names: list[str] = []
        for name, resolved in resolved_all.items():
            print(f"Installing environment '{name}'...")
            install_environment(ctx, resolved, force_reinstall=force, dry_run=dry_run)
            installed_names.append(name)
            print(f"  -> {ctx.env_prefix(name)}")
        if not dry_run:
            generate_lockfile(ctx, env_names=installed_names)
        print(f"\n{len(resolved_all)} environment(s) installed.")

    return 0


def _install_locked(ctx: WorkspaceContext, config: object, env_name: str | None) -> int:
    """Install environments from existing lockfiles (no solving)."""
    if env_name:
        print(f"Installing environment '{env_name}' from lockfile...")
        install_from_lockfile(ctx, env_name)
        print(f"Environment '{env_name}' is ready at {ctx.env_prefix(env_name)}")
    else:
        resolved_all = resolve_all_environments(config, ctx.platform)
        for name in resolved_all:
            print(f"Installing environment '{name}' from lockfile...")
            install_from_lockfile(ctx, name)
            print(f"  -> {ctx.env_prefix(name)}")
        print(f"\n{len(resolved_all)} environment(s) installed from lockfiles.")

    return 0
