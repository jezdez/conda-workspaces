"""Workspace manifest detection and parser registry.

Search order
------------
1. ``conda.toml``     – conda-native workspace format
2. ``pixi.toml``      – pixi-native workspace format (compatibility)
3. ``pyproject.toml`` – pixi or conda tables embedded

The first file that exists *and* contains workspace configuration wins.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from ..exceptions import WorkspaceNotFoundError, WorkspaceParseError
from .toml import CondaTomlParser
from .pixi_toml import PixiTomlParser
from .pyproject_toml import PyprojectTomlParser

if TYPE_CHECKING:
    from ..models import WorkspaceConfig
    from .base import WorkspaceParser

# Parser instances in search priority order
_PARSERS: list[WorkspaceParser] = [
    CondaTomlParser(),
    PixiTomlParser(),
    PyprojectTomlParser(),
]

# File names to look for, in priority order
_SEARCH_FILES: list[str] = [
    "conda.toml",
    "pixi.toml",
    "pyproject.toml",
]


def detect_workspace_file(
    start_dir: str | Path | None = None,
) -> Path:
    """Walk up from *start_dir* to find a workspace manifest.

    Returns the path to the first matching file.
    Raises ``WorkspaceNotFoundError`` if none is found.
    """
    if start_dir is None:
        start_dir = Path.cwd()
    else:
        start_dir = Path(start_dir)

    current = start_dir.resolve()
    while True:
        for fname in _SEARCH_FILES:
            candidate = current / fname
            if candidate.is_file():
                for parser in _PARSERS:
                    if parser.can_handle(candidate) and parser.has_workspace(
                        candidate
                    ):
                        return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent

    raise WorkspaceNotFoundError(start_dir)


def find_parser(path: Path) -> WorkspaceParser:
    """Return the parser that can handle *path*.

    Raises ``WorkspaceParseError`` if no parser matches.
    """
    for parser in _PARSERS:
        if parser.can_handle(path):
            return parser
    raise WorkspaceParseError(path, f"No parser available for '{path.name}'")


@lru_cache(maxsize=4)
def _cached_parse(path_str: str) -> WorkspaceConfig:
    """LRU-cached wrapper around parser dispatch."""
    path = Path(path_str)
    parser = find_parser(path)
    return parser.parse(path)


def detect_and_parse(
    start_dir: str | Path | None = None,
) -> tuple[Path, WorkspaceConfig]:
    """Detect the workspace manifest and parse it.

    Returns ``(manifest_path, workspace_config)``.
    """
    path = detect_workspace_file(start_dir)
    config = _cached_parse(str(path))
    return path, config
