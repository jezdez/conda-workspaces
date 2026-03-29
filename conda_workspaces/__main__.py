"""Standalone CLI entry points for ``cw`` and ``ct``.

``cw`` runs ``conda workspace`` commands::

    cw init
    cw install
    cw list
    cw add -e dev pytest

``ct`` runs ``conda task`` commands::

    ct run test
    ct list
    ct add lint "ruff check ."
"""

from __future__ import annotations


def main(args: list[str] | None = None) -> None:
    """Entry point for the ``cw`` console script."""
    from .cli.main import execute_workspace, generate_workspace_parser

    parser = generate_workspace_parser()
    parser.prog = "cw"

    parsed = parser.parse_args(args)
    raise SystemExit(execute_workspace(parsed))


def main_task(args: list[str] | None = None) -> None:
    """Entry point for the ``ct`` console script."""
    from .cli.main import execute_task, generate_task_parser

    parser = generate_task_parser()
    parser.prog = "ct"

    parsed = parser.parse_args(args)
    raise SystemExit(execute_task(parsed))


if __name__ == "__main__":
    main()
