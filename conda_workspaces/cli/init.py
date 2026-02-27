"""``conda workspace init`` — scaffold a new workspace manifest."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import tomlkit
from conda.base.context import context as conda_context

from ..exceptions import ManifestExistsError

if TYPE_CHECKING:
    import argparse


def execute_init(args: argparse.Namespace) -> int:
    """Create a new workspace manifest in the current directory."""
    fmt = args.manifest_format
    name = args.name or Path.cwd().name
    channels = args.channels or ["conda-forge"]

    if args.platforms:
        platforms = args.platforms
    else:
        platforms = _detect_platforms()

    if fmt == "pixi":
        return _write_pixi_toml(name, channels, platforms)
    elif fmt == "conda":
        return _write_conda_toml(name, channels, platforms)
    elif fmt == "pyproject":
        return _write_pyproject_toml(name, channels, platforms)

    return 1


def _detect_platforms() -> list[str]:
    """Auto-detect a reasonable set of platforms."""
    current = conda_context.subdir
    # Include a sensible default set based on current platform
    defaults = {"linux-64", "osx-64", "osx-arm64", "win-64"}
    defaults.add(current)
    return sorted(defaults)


def _write_pixi_toml(name: str, channels: list[str], platforms: list[str]) -> int:
    path = Path("pixi.toml")
    if path.exists():
        raise ManifestExistsError(path)

    doc = tomlkit.document()

    ws = tomlkit.table()
    ws.add("name", name)
    ws.add("version", "0.1.0")
    ws.add("channels", channels)
    ws.add("platforms", platforms)
    doc.add("workspace", ws)

    deps = tomlkit.table()
    doc.add("dependencies", deps)

    path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    print(f"Created {path}")
    return 0


def _write_conda_toml(name: str, channels: list[str], platforms: list[str]) -> int:
    path = Path("conda.toml")
    if path.exists():
        raise ManifestExistsError(path)

    doc = tomlkit.document()

    ws = tomlkit.table()
    ws.add("name", name)
    ws.add("version", "0.1.0")
    ws.add("channels", channels)
    ws.add("platforms", platforms)
    doc.add("workspace", ws)

    deps = tomlkit.table()
    doc.add("dependencies", deps)

    path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    print(f"Created {path}")
    return 0


def _write_pyproject_toml(name: str, channels: list[str], platforms: list[str]) -> int:
    path = Path("pyproject.toml")

    if path.exists():
        text = path.read_text(encoding="utf-8")
        doc = tomlkit.loads(text)
    else:
        doc = tomlkit.document()

    tool = doc.setdefault("tool", tomlkit.table())
    if "pixi" in tool:
        raise ManifestExistsError("[tool.pixi] in pyproject.toml")

    pixi = tomlkit.table()
    ws = tomlkit.table()
    ws.add("channels", channels)
    ws.add("platforms", platforms)
    pixi.add("workspace", ws)
    pixi.add("dependencies", tomlkit.table())
    tool.add("pixi", pixi)

    path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    print(f"{'Updated' if path.exists() else 'Created'} {path}")
    return 0
