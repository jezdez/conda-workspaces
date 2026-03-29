"""Shared fixtures for CLI tests."""

from __future__ import annotations

import argparse
from io import StringIO
from typing import TYPE_CHECKING

import pytest
from rich.console import Console

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def pixi_workspace(tmp_path: Path) -> Path:
    """Create a minimal pixi.toml workspace and return tmp_path."""
    content = """\
[workspace]
name = "cli-test"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[dependencies]
python = ">=3.10"

[feature.test.dependencies]
pytest = ">=8.0"

[environments]
default = []
test = {features = ["test"]}
"""
    (tmp_path / "pixi.toml").write_text(content, encoding="utf-8")
    return tmp_path


@pytest.fixture
def rich_console() -> Console:
    """A Console that writes to a StringIO buffer for test capture.

    Read captured output via ``rich_console.file.getvalue()``.
    """
    return Console(file=StringIO(), width=200)


def make_args(defaults: dict, **overrides) -> argparse.Namespace:
    """Build an argparse.Namespace from *defaults* merged with *overrides*."""
    return argparse.Namespace(**{**defaults, **overrides})
