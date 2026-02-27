"""Standalone CLI entry point for ``cw`` (short for ``conda workspace``).

This module allows running conda-workspaces without going through the
conda plugin dispatch::

    cw init
    cw install
    cw list
    cw add -e dev pytest

It reuses the same parser and execute logic as ``conda workspace``.
"""

from __future__ import annotations

import sys


def main(args: list[str] | None = None) -> None:
    """Entry point for the ``cw`` console script."""
    from .cli.main import execute, generate_parser

    parser = generate_parser()
    parser.prog = "cw"

    parsed = parser.parse_args(args)
    raise SystemExit(execute(parsed))


if __name__ == "__main__":
    main()
