"""Handler for ``conda task add``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ...models import Task, TaskDependency
from ...parsers import detect_task_file, find_parser
from ...parsers.toml import CondaTomlParser

if TYPE_CHECKING:
    import argparse


def execute_add(args: argparse.Namespace) -> int:
    """Execute the ``conda task add`` subcommand."""
    file_path = getattr(args, "file", None)
    if file_path is None:
        file_path = detect_task_file()
        if file_path is None:
            file_path = Path.cwd() / "conda.toml"

    try:
        parser = find_parser(file_path)
    except Exception:
        parser = CondaTomlParser()

    depends = [TaskDependency(task=d) for d in (args.depends_on or [])]
    task = Task(
        name=args.task_name,
        cmd=args.cmd,
        depends_on=depends,
        description=args.description,
    )

    dry_run = getattr(args, "dry_run", False)
    quiet = getattr(args, "quiet", False)

    if dry_run:
        print(f"  [dry-run] Would add task '{args.task_name}' to {file_path}")
        return 0

    parser.add_task(file_path, args.task_name, task)
    if not quiet:
        print(f"  Added task '{args.task_name}' to {file_path}")
    return 0
