"""``conda workspace info`` — show environment details."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ..context import WorkspaceContext
from ..envs import get_environment_info
from ..parsers import detect_and_parse
from ..resolver import resolve_environment

if TYPE_CHECKING:
    import argparse


def execute_info(args: argparse.Namespace) -> int:
    """Show details about an environment."""
    manifest_path = getattr(args, "file", None)
    _, config = detect_and_parse(manifest_path)
    ctx = WorkspaceContext(config)

    env_name = args.env_name
    json_output = getattr(args, "json", False)

    resolved = resolve_environment(config, env_name, ctx.platform)
    install_info = get_environment_info(ctx, env_name)

    info = {
        "name": env_name,
        "prefix": str(ctx.env_prefix(env_name)),
        "installed": install_info["exists"],
        "channels": [ch.canonical_name for ch in resolved.channels],
        "platforms": resolved.platforms,
        "solve_group": resolved.solve_group,
        "conda_dependencies": {
            name: dep.conda_build_form()
            for name, dep in resolved.conda_dependencies.items()
        },
        "pypi_dependencies": {
            name: str(dep) for name, dep in resolved.pypi_dependencies.items()
        },
    }

    if install_info["exists"]:
        info["packages_installed"] = install_info.get("packages", 0)

    if json_output:
        print(json.dumps(info, indent=2))
    else:
        print(f"Environment: {info['name']}")
        print(f"Prefix:      {info['prefix']}")
        print(f"Installed:   {'yes' if info['installed'] else 'no'}")
        if info["installed"]:
            print(f"Packages:    {info.get('packages_installed', '?')}")
        print(f"Channels:    {', '.join(info['channels']) or '(none)'}")
        print(f"Platforms:   {', '.join(info['platforms']) or '(all)'}")
        if info["solve_group"]:
            print(f"Solve group: {info['solve_group']}")

        if info["conda_dependencies"]:
            print("\nConda dependencies:")
            for name, spec in sorted(info["conda_dependencies"].items()):
                print(f"  - {spec}")

        if info["pypi_dependencies"]:
            print("\nPyPI dependencies:")
            for name, spec in sorted(info["pypi_dependencies"].items()):
                print(f"  - {spec}")

    return 0
