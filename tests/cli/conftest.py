"""Shared fixtures for CLI tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

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
default = {solve-group = "default"}
test = {features = ["test"], solve-group = "default"}
"""
    (tmp_path / "pixi.toml").write_text(content, encoding="utf-8")
    return tmp_path
