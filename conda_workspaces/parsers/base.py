"""Abstract base class for workspace manifest parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import ClassVar

    from ..models import WorkspaceConfig


class WorkspaceParser(ABC):
    """Interface that every workspace manifest parser must implement.

    Subclasses declare which files they can handle via *filenames*
    (exact names) and *extensions* (suffix matching).  The registry
    in ``parsers/__init__.py`` uses these to auto-detect the right
    parser for a given directory.
    """

    filenames: ClassVar[tuple[str, ...]] = ()
    extensions: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True if this parser can read *path*."""

    @abstractmethod
    def parse(self, path: Path) -> WorkspaceConfig:
        """Parse *path* and return a ``WorkspaceConfig``."""

    @abstractmethod
    def has_workspace(self, path: Path) -> bool:
        """Return True if *path* contains workspace configuration.

        Some files (e.g. ``pyproject.toml``) may exist without
        workspace tables.  This method checks for the actual presence
        of workspace data.
        """
