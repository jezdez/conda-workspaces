"""Manifest importers for ``conda workspace import``.

Each importer converts a foreign manifest format into a
``tomlkit.Document`` representing a ``conda.toml`` workspace manifest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .anaconda_project import AnacondaProjectImporter
from .conda_project import CondaProjectImporter
from .environment_yml import EnvironmentYmlImporter
from .pixi_toml import PixiTomlImporter
from .pyproject_toml import PyprojectTomlImporter

if TYPE_CHECKING:
    from pathlib import Path

    import tomlkit

    from .base import ManifestImporter

_IMPORTERS: list[ManifestImporter] = [
    EnvironmentYmlImporter(),
    AnacondaProjectImporter(),
    CondaProjectImporter(),
    PixiTomlImporter(),
    PyprojectTomlImporter(),
]


def detect_format(path: Path) -> str:
    """Return the format identifier for *path* based on its filename.

    Raises ``ValueError`` if the filename is not recognised.
    """
    for importer in _IMPORTERS:
        if importer.can_handle(path):
            return type(importer).__name__
    supported = ", ".join(
        fn for imp in _IMPORTERS for fn in imp.filenames
    )
    raise ValueError(
        f"Unrecognised manifest format: '{path.name}'. "
        f"Supported filenames: {supported}"
    )


def find_importer(path: Path) -> ManifestImporter:
    """Return the importer that can handle *path*.

    Raises ``ValueError`` if no importer matches.
    """
    for importer in _IMPORTERS:
        if importer.can_handle(path):
            return importer
    supported = ", ".join(
        fn for imp in _IMPORTERS for fn in imp.filenames
    )
    raise ValueError(
        f"Unrecognised manifest format: '{path.name}'. "
        f"Supported filenames: {supported}"
    )


def import_manifest(path: Path) -> tomlkit.TOMLDocument:
    """Import *path* and return a ``conda.toml``-shaped TOML document.

    Auto-detects the format from the filename and dispatches to the
    appropriate importer.
    """
    return find_importer(path).convert(path)
