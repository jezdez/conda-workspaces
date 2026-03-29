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

    console.print(f"Tasks from {task_file}:\n")

    table = Table(show_edge=False, pad_edge=False)
    table.add_column("Name")
    table.add_column("Command")
    table.add_column("Description")
    table.add_column("Dependencies")

    for name, task in visible_tasks.items():
        cmd_str = ""
        if task.cmd is not None:
            cmd_str = task.cmd if isinstance(task.cmd, str) else " ".join(task.cmd)
        elif task.is_alias:
            cmd_str = "(alias)"

        desc = task.description or ""
        deps = ", ".join(d.task for d in task.depends_on) if task.depends_on else ""
        table.add_row(name, cmd_str, desc, deps)

    console.print()
    console.print(table)

    return 0
