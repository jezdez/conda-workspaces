"""Shared status markers and helpers for CLI output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape as _escape

if TYPE_CHECKING:
    from rich.console import Console

RUNNING = "[bold blue]●[/bold blue]"
DONE = "[bold green]✓[/bold green]"
FAILED = "[bold red]✗[/bold red]"
CACHED = "[dim cyan]○[/dim cyan]"
DRY_RUN = "[bold yellow]◌[/bold yellow]"


def _label(
    marker: str,
    name: str,
    *,
    detail: str | None = None,
    suffix: str | None = None,
) -> str:
    """Build a Rich markup status line."""
    text = f"{marker} {_escape(name)}"
    if detail:
        text += f" ── [dim]{_escape(detail)}[/dim]"
    if suffix:
        text += f" [dim]({suffix})[/dim]"
    return text


def _print(
    console: Console,
    marker: str,
    name: str,
    *,
    detail: str | None = None,
    suffix: str | None = None,
) -> None:
    console.print(_label(marker, name, detail=detail, suffix=suffix))


def done(
    console: Console,
    name: str,
    *,
    detail: str | None = None,
    suffix: str | None = None,
) -> None:
    """Print a ``✓`` status line."""
    _print(console, DONE, name, detail=detail, suffix=suffix)


def running(
    console: Console,
    name: str,
    *,
    detail: str | None = None,
    suffix: str | None = None,
) -> None:
    """Print a ``●`` status line."""
    _print(console, RUNNING, name, detail=detail, suffix=suffix)


def failed(
    console: Console,
    name: str,
    *,
    detail: str | None = None,
    suffix: str | None = None,
) -> None:
    """Print a ``✗`` status line."""
    _print(console, FAILED, name, detail=detail, suffix=suffix)


def cached(
    console: Console,
    name: str,
    *,
    suffix: str = "cached",
) -> None:
    """Print a ``○`` status line (defaults to ``(cached)`` suffix)."""
    _print(console, CACHED, name, suffix=suffix)


def dry_run(
    console: Console,
    name: str,
    *,
    detail: str | None = None,
    suffix: str | None = None,
) -> None:
    """Print a ``◌`` status line."""
    _print(console, DRY_RUN, name, detail=detail, suffix=suffix)


def dry_run_label(
    name: str,
    *,
    detail: str | None = None,
) -> str:
    """Build a ``◌`` label string for Rich Tree nodes."""
    return _label(DRY_RUN, name, detail=detail)
