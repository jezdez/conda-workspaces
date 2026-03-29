"""CLI package for ``conda workspace`` and ``conda task``."""

from __future__ import annotations

from .main import (
    configure_task_parser,
    configure_workspace_parser,
    execute_task,
    execute_workspace,
    generate_task_parser,
    generate_workspace_parser,
)

__all__ = [
    "configure_task_parser",
    "configure_workspace_parser",
    "execute_task",
    "execute_workspace",
    "generate_task_parser",
    "generate_workspace_parser",
]
