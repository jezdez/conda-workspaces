"""``conda workspace list`` — list workspace environments."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from ..context import WorkspaceContext
from ..envs import list_installed_environments
from ..parsers import detect_and_parse

if TYPE_CHECKING:
    import argparse


def execute_list(args: argparse.Namespace) -> int:
    """List environments defined in the workspace."""
    manifest_path = getattr(args, "file", None)
    _, config = detect_and_parse(manifest_path)
    ctx = WorkspaceContext(config)

    installed_only = getattr(args, "installed", False)
    json_output = getattr(args, "json", False)

    installed = set(list_installed_environments(ctx))

    rows: list[dict[str, str | bool | list[str]]] = []
    for name, env in sorted(config.environments.items()):
        if installed_only and name not in installed:
            continue
        rows.append(
            {
                "name": name,
                "features": env.features,
                "solve_group": env.solve_group or "",
                "installed": name in installed,
            }
        )

    if json_output:
        print(json.dumps(rows, indent=2))
    else:
        if not rows:
            print("No environments found.")
            return 0

        # Header
        print(f"{'Name':<20} {'Features':<30} {'Solve Group':<15} {'Installed'}")
        print("-" * 75)
        for row in rows:
            feats = ", ".join(row["features"]) if row["features"] else "(default)"  # type: ignore[arg-type]
            status = "yes" if row["installed"] else "no"
            print(f"{row['name']:<20} {feats:<30} {row['solve_group']:<15} {status}")

    return 0
