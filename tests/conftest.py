"""Shared test fixtures for conda-workspaces."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from conda_workspaces.models import (
    Channel,
    Environment,
    Feature,
    MatchSpec,
    WorkspaceConfig,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def sample_pixi_toml(tmp_path: Path) -> Path:
    """Create a minimal pixi.toml in tmp_path and return its path."""
    content = """\
[workspace]
name = "test-project"
version = "0.1.0"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64"]

[dependencies]
python = ">=3.10"
numpy = ">=1.24"

[feature.test.dependencies]
pytest = ">=8.0"

[feature.docs.dependencies]
sphinx = ">=7.0"

[environments]
default = {solve-group = "default"}
test = {features = ["test"], solve-group = "default"}
docs = {features = ["docs"]}
"""
    path = tmp_path / "pixi.toml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_pyproject_toml(tmp_path: Path) -> Path:
    """Create a pyproject.toml with [tool.pixi.*] tables."""
    content = """\
[project]
name = "my-project"
version = "1.0.0"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64", "win-64"]

[tool.pixi.dependencies]
python = ">=3.11"

[tool.pixi.feature.test.dependencies]
pytest = ">=8.0"
pytest-cov = ">=4.0"

[tool.pixi.environments]
test = {features = ["test"], solve-group = "default"}
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_config() -> WorkspaceConfig:
    """Return a pre-built WorkspaceConfig for unit tests."""
    default_feat = Feature(
        name="default",
        conda_dependencies={
            "python": MatchSpec("python >=3.10"),
            "numpy": MatchSpec("numpy >=1.24"),
        },
    )
    test_feat = Feature(
        name="test",
        conda_dependencies={
            "pytest": MatchSpec("pytest >=8.0"),
        },
    )
    docs_feat = Feature(
        name="docs",
        conda_dependencies={
            "sphinx": MatchSpec("sphinx >=7.0"),
        },
    )

    return WorkspaceConfig(
        name="test-project",
        version="0.1.0",
        channels=[Channel("conda-forge")],
        platforms=["linux-64", "osx-arm64"],
        features={
            "default": default_feat,
            "test": test_feat,
            "docs": docs_feat,
        },
        environments={
            "default": Environment(name="default", solve_group="default"),
            "test": Environment(name="test", features=["test"], solve_group="default"),
            "docs": Environment(name="docs", features=["docs"]),
        },
        root="/tmp/test-project",
        manifest_path="/tmp/test-project/pixi.toml",
    )
