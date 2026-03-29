"""Abstract base class for manifest parsers (workspaces and tasks)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from typing import ClassVar

    from ..models import Task, WorkspaceConfig


class ManifestParser(ABC):
    """Interface that every manifest parser must implement.

    Each parser handles one file format (``conda.toml``, ``pixi.toml``,
    or ``pyproject.toml``).  Subclasses declare which files they can
    handle via *filenames* and *extensions*.  The registry in
    ``parsers/__init__.py`` uses these to auto-detect the right parser.

    A single parser instance handles both workspace configuration and
    task definitions from the same file.
    """

    filenames: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True if this parser can read *path*."""

    @abstractmethod
    def has_workspace(self, path: Path) -> bool:
        """Return True if *path* contains workspace configuration."""

    @abstractmethod
    def parse(self, path: Path) -> WorkspaceConfig:
        """Parse *path* and return a ``WorkspaceConfig``."""

    def has_tasks(self, path: Path) -> bool:
        """Return True if *path* contains task definitions."""
        return False

    def parse_tasks(self, path: Path) -> dict[str, Task]:
        """Parse *path* and return a mapping of task-name to Task."""
        return {}

    def add_task(self, path: Path, name: str, task: Task) -> None:
        """Persist a new task definition into *path*."""
        raise NotImplementedError(
            f"Writing tasks to {path.name} is not supported. Use conda.toml instead."
        )

    def remove_task(self, path: Path, name: str) -> None:
        """Remove the task named *name* from *path*."""
        raise NotImplementedError(
            f"Writing tasks to {path.name} is not supported. Use conda.toml instead."
        )
