"""Tests for conda_workspaces.parsers.pixi_toml (pixi.toml parser)."""

from __future__ import annotations

from pathlib import Path

import pytest

from conda_workspaces.parsers.pixi_toml import PixiTomlParser


@pytest.fixture
def parser():
    return PixiTomlParser()


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("pixi.toml", True),
        ("pyproject.toml", False),
        ("conda.toml", False),
    ],
    ids=["pixi-toml", "pyproject-toml", "conda-toml"],
)
def test_can_handle(parser, filename, expected):
    assert parser.can_handle(Path(filename)) is expected


def test_has_workspace(parser, sample_pixi_toml):
    assert parser.has_workspace(sample_pixi_toml)


def test_has_workspace_missing_file(parser, tmp_path):
    assert not parser.has_workspace(tmp_path / "pixi.toml")


def test_parse_basic(parser, sample_pixi_toml):
    config = parser.parse(sample_pixi_toml)
    assert config.name == "test-project"
    assert config.version == "0.1.0"
    assert len(config.channels) == 1
    assert config.channels[0].canonical_name == "conda-forge"
    assert "linux-64" in config.platforms
    assert "osx-arm64" in config.platforms


def test_parse_default_dependencies(parser, sample_pixi_toml):
    config = parser.parse(sample_pixi_toml)
    default = config.features["default"]
    assert "python" in default.conda_dependencies
    assert str(default.conda_dependencies["python"].version) == ">=3.10"
    assert "numpy" in default.conda_dependencies


def test_parse_features(parser, sample_pixi_toml):
    config = parser.parse(sample_pixi_toml)
    assert "test" in config.features
    assert "docs" in config.features
    test_feat = config.features["test"]
    assert "pytest" in test_feat.conda_dependencies


def test_parse_environments(parser, sample_pixi_toml):
    config = parser.parse(sample_pixi_toml)
    assert "default" in config.environments
    assert "test" in config.environments
    assert "docs" in config.environments
    test_env = config.environments["test"]
    assert test_env.features == ["test"]
    assert test_env.solve_group == "default"


def test_parse_with_targets(tmp_path):
    content = """\
[workspace]
name = "target-test"
channels = ["conda-forge"]
platforms = ["linux-64", "osx-arm64"]

[dependencies]
python = ">=3.10"

[target.linux-64.dependencies]
gcc = ">=12"
"""
    path = tmp_path / "pixi.toml"
    path.write_text(content, encoding="utf-8")

    parser = PixiTomlParser()
    config = parser.parse(path)
    default = config.features["default"]
    assert "linux-64" in default.target_conda_dependencies
    assert "gcc" in default.target_conda_dependencies["linux-64"]


def test_parse_with_pypi_deps(tmp_path):
    content = """\
[workspace]
name = "pypi-test"
channels = ["conda-forge"]
platforms = ["linux-64"]

[dependencies]
python = ">=3.10"

[pypi-dependencies]
requests = ">=2.28"
"""
    path = tmp_path / "pixi.toml"
    path.write_text(content, encoding="utf-8")

    parser = PixiTomlParser()
    config = parser.parse(path)
    default = config.features["default"]
    assert "requests" in default.pypi_dependencies


def test_parse_activation(tmp_path):
    content = """\
[workspace]
name = "activation-test"
channels = ["conda-forge"]
platforms = ["linux-64"]

[activation]
scripts = ["setup.sh"]

[activation.env]
MY_VAR = "hello"
"""
    path = tmp_path / "pixi.toml"
    path.write_text(content, encoding="utf-8")

    parser = PixiTomlParser()
    config = parser.parse(path)
    default = config.features["default"]
    assert default.activation_scripts == ["setup.sh"]
    assert default.activation_env == {"MY_VAR": "hello"}


def test_parse_environment_as_list(tmp_path):
    content = """\
[workspace]
name = "list-env-test"
channels = ["conda-forge"]
platforms = ["linux-64"]

[environments]
dev = ["test", "lint"]
"""
    path = tmp_path / "pixi.toml"
    path.write_text(content, encoding="utf-8")

    parser = PixiTomlParser()
    config = parser.parse(path)
    env = config.environments["dev"]
    assert env.features == ["test", "lint"]
