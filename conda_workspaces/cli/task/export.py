"""Handler for ``conda task export``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...parsers import detect_and_parse_tasks
from ...parsers.toml import tasks_to_toml

if TYPE_CHECKING:
    import argparse
    from pathlib import Path


def execute_export(args: argparse.Namespace) -> int:
    """Execute the ``conda task export`` subcommand."""
    file_path = getattr(args, "file", None)
    task_file, tasks = detect_and_parse_tasks(file_path=file_path)

    quiet = getattr(args, "quiet", False)
    output: Path | None = getattr(args, "output", None)

    text = tasks_to_toml(tasks)

    if output is not None:
        output.write_text(text, encoding="utf-8")
        if not quiet:
            print(f"  Exported {len(tasks)} task(s) from {task_file} to {output}")
    else:
        print(text, end="")

    return 0
