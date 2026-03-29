"""Fixtures for parser tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def task_pixi_toml(tmp_project: Path) -> Path:
    """Create a sample pixi.toml with tasks for testing."""
    content = """\
[tasks]
build = "make build"
test = { cmd = "pytest", depends-on = ["build"] }
lint = { cmd = "ruff check .", description = "Lint the code" }

[target.win-64.tasks]
build = "nmake build"
"""
    path = tmp_project / "pixi.toml"
    path.write_text(content)
    return path


@pytest.fixture
def task_pyproject(tmp_project: Path) -> Path:
    """Create a sample pyproject.toml with task section."""
    content = """\
[project]
name = "example"

[tool.conda.tasks]
build = "make build"

[tool.conda.tasks.test]
cmd = "pytest"
depends-on = ["build"]

[tool.conda.target.win-64.tasks]
build = "nmake build"
"""
    path = tmp_project / "pyproject.toml"
    path.write_text(content)
    return path


@pytest.fixture
def task_conda_toml(tmp_project: Path) -> Path:
    """Create a sample conda.toml with tasks for testing."""
    content = """\
[tasks]
build = { cmd = "make build", depends-on = ["configure"] }
configure = "cmake ."
test = { cmd = "pytest", depends-on = ["build"] }

[target.win-64.tasks]
build = "nmake build"
"""
    path = tmp_project / "conda.toml"
    path.write_text(content)
    return path
