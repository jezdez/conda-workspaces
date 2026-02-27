"""Tests for conda_workspaces.parsers.pyproject_toml."""

from __future__ import annotations

from pathlib import Path

import pytest

from conda_workspaces.parsers.pyproject_toml import PyprojectTomlParser


@pytest.fixture
def parser():
    return PyprojectTomlParser()


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("pyproject.toml", True),
        ("pixi.toml", False),
        ("conda.toml", False),
    ],
    ids=["pyproject-toml", "pixi-toml", "conda-toml"],
)
def test_can_handle(parser, filename, expected):
    assert parser.can_handle(Path(filename)) is expected


def test_has_workspace(parser, sample_pyproject_toml):
    assert parser.has_workspace(sample_pyproject_toml)


def test_has_workspace_no_pixi(parser, tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "foo"\n', encoding="utf-8")
    assert not parser.has_workspace(path)


def test_parse_basic(parser, sample_pyproject_toml):
    config = parser.parse(sample_pyproject_toml)
    assert config.name == "my-project"
    assert len(config.channels) == 1
    assert "linux-64" in config.platforms


def test_parse_dependencies(parser, sample_pyproject_toml):
    config = parser.parse(sample_pyproject_toml)
    default = config.features["default"]
    assert "python" in default.conda_dependencies
    assert str(default.conda_dependencies["python"].version) == ">=3.11"


def test_parse_features(parser, sample_pyproject_toml):
    config = parser.parse(sample_pyproject_toml)
    assert "test" in config.features
    test_feat = config.features["test"]
    assert "pytest" in test_feat.conda_dependencies
    assert "pytest-cov" in test_feat.conda_dependencies


def test_parse_environments(parser, sample_pyproject_toml):
    config = parser.parse(sample_pyproject_toml)
    assert "test" in config.environments
    test_env = config.environments["test"]
    assert test_env.features == ["test"]
    assert test_env.solve_group == "default"


@pytest.mark.parametrize(
    "table_key, dep_key",
    [
        ("tool.conda", "tool.conda"),
        ("tool.conda-workspaces", "tool.conda-workspaces"),
    ],
    ids=["conda-table", "conda-workspaces-table"],
)
def test_alternative_tables(parser, tmp_path, table_key, dep_key):
    content = f"""\
[project]
name = "alt-table-project"

[{table_key}.workspace]
channels = ["conda-forge"]
platforms = ["linux-64"]

[{dep_key}.dependencies]
python = ">=3.12"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")

    assert parser.has_workspace(path)
    config = parser.parse(path)
    assert config.name == "alt-table-project"
    default = config.features["default"]
    assert "python" in default.conda_dependencies


def test_no_workspace_raises(parser, tmp_path):
    from conda_workspaces.exceptions import WorkspaceParseError

    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "foo"\n', encoding="utf-8")
    with pytest.raises(WorkspaceParseError):
        parser.parse(path)


def test_conda_table_priority_over_pixi(parser, tmp_path):
    """[tool.conda] should win over [tool.pixi]."""
    content = """\
[project]
name = "priority-test"

[tool.conda.workspace]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tool.conda.dependencies]
python = ">=3.12"

[tool.pixi.workspace]
channels = ["defaults"]
platforms = ["win-64"]

[tool.pixi.dependencies]
python = ">=3.10"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")

    config = parser.parse(path)
    # Should use conda table (>=3.12), not pixi (>=3.10)
    default = config.features["default"]
    assert str(default.conda_dependencies["python"].version) == ">=3.12"
