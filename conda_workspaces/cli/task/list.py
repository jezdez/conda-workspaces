"""Handler for ``conda task list``."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from ...parsers import detect_and_parse_tasks

if TYPE_CHECKING:
    import argparse


def execute_list(args: argparse.Namespace, *, console: Console | None = None) -> int:
    """Execute the ``conda task list`` subcommand."""
    file_path = getattr(args, "file", None)
    task_file, tasks = detect_and_parse_tasks(file_path=file_path)

    if console is None:
        console = Console()

    use_json = getattr(args, "json", False)

    visible_tasks = {name: t for name, t in sorted(tasks.items()) if not t.is_hidden}

    if use_json:
        data: dict[str, dict[str, object]] = {}
        for name, task in visible_tasks.items():
            entry: dict[str, object] = {"name": name}
            if task.cmd is not None:
                entry["cmd"] = task.cmd
            if task.description:
                entry["description"] = task.description
            if task.depends_on:
                entry["depends_on"] = [d.task for d in task.depends_on]
            if task.is_alias:
                entry["alias"] = True
            data[name] = entry

        console.print_json(json.dumps({"tasks": data, "file": str(task_file)}))
        return 0

    if not visible_tasks:
        console.print(f"No tasks defined in {task_file}")
        return 0

    console.print(f"Tasks from {task_file}:")

    has_descriptions = any(t.description for t in visible_tasks.values())

    table = Table(show_edge=False, pad_edge=False, show_header=False)
    table.add_column()
    if has_descriptions:
        table.add_column()

    for name, task in visible_tasks.items():
        if has_descriptions:
            table.add_row(name, task.description or "")
        else:
            table.add_row(name)

    console.print(table)

    return 0
