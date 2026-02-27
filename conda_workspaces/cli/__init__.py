"""CLI package for ``conda workspace``."""

from __future__ import annotations

from .main import configure_parser, execute, generate_parser

__all__ = ["configure_parser", "execute", "generate_parser"]
