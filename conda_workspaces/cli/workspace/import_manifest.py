"""Handler for ``conda workspace import``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import tomlkit
from conda.exceptions import CondaSystemExit, DryRunExit
from conda.reporters import confirm_yn
from rich.console import Console

from ...importers import import_manifest

if TYPE_CHECKING:
    import argparse


def execute_import(
    args: argparse.Namespace, *, console: Console | None = None
) -> int:
    """Execute the ``conda workspace import`` subcommand."""
    if console is None:
        console = Console(highlight=False)

    source: Path = args.file
    if not source.exists():
        console.print(f"[bold red]Error:[/bold red] {source} not found")
        return 1

    quiet = getattr(args, "quiet", False)
    dry_run = getattr(args, "dry_run", False)
    output: Path = getattr(args, "output", None) or Path("conda.toml")

    doc = import_manifest(source)
    text = tomlkit.dumps(doc)

    if dry_run:
        print(text, end="")
        raise DryRunExit()

    if output.is_file():
        try:
            confirm_yn(f"Overwrite {output}?")
        except (CondaSystemExit, DryRunExit):
            return 0

    output.write_text(text, encoding="utf-8")
    if not quiet:
        console.print(
            f"[bold cyan]Imported[/bold cyan] [bold]{source}[/bold] "
            f"-> [bold]{output}[/bold]"
        )

    return 0
