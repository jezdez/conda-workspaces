"""Tests for workspace manifest detection."""

from __future__ import annotations

from pathlib import Path

import pytest

from conda_workspaces.exceptions import WorkspaceNotFoundError, WorkspaceParseError
from conda_workspaces.parsers import (
    _cached_parse,
    detect_and_parse,
    detect_workspace_file,
    find_parser,
)
from conda_workspaces.parsers.pixi_toml import PixiTomlParser
from conda_workspaces.parsers.pyproject_toml import PyprojectTomlParser
from conda_workspaces.parsers.toml import CondaTomlParser


@pytest.mark.parametrize(
    "fixture_name",
    ["sample_pixi_toml", "sample_pyproject_toml"],
    ids=["pixi-toml", "pyproject-toml"],
)
def test_detect_manifest(fixture_name, request):
    manifest = request.getfixturevalue(fixture_name)
    path = detect_workspace_file(manifest.parent)
    assert path == manifest


def test_detect_walks_up(sample_pixi_toml):
    subdir = sample_pixi_toml.parent / "src" / "pkg"
    subdir.mkdir(parents=True)
    path = detect_workspace_file(subdir)
    assert path == sample_pixi_toml


def test_detect_not_found(tmp_path):
    with pytest.raises(WorkspaceNotFoundError):
        detect_workspace_file(tmp_path)


def test_conda_toml_priority_over_pixi(tmp_path):
    """conda.toml should be preferred when both exist."""
    conda = tmp_path / "conda.toml"
    conda.write_text(
        '[workspace]\nname = "conda"\nchannels = ["conda-forge"]\nplatforms = ["linux-64"]\n',
        encoding="utf-8",
    )
    pixi = tmp_path / "pixi.toml"
    pixi.write_text(
        '[workspace]\nname = "pixi"\nchannels = ["conda-forge"]\nplatforms = ["linux-64"]\n',
        encoding="utf-8",
    )
    path = detect_workspace_file(tmp_path)
    assert path.name == "conda.toml"


def test_pixi_toml_priority_over_pyproject(tmp_path):
    """pixi.toml should be preferred over pyproject.toml."""
    pixi = tmp_path / "pixi.toml"
    pixi.write_text(
        '[workspace]\nname = "pixi"\nchannels = ["conda-forge"]\nplatforms = ["linux-64"]\n',
        encoding="utf-8",
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[tool.pixi.workspace]\nchannels = ["conda-forge"]\nplatforms = ["linux-64"]\n',
        encoding="utf-8",
    )
    path = detect_workspace_file(tmp_path)
    assert path.name == "pixi.toml"


def test_conda_toml(tmp_path):
    path = tmp_path / "conda.toml"
    path.write_text(
        '[workspace]\nname = "cw"\nchannels = ["conda-forge"]\nplatforms = ["linux-64"]\n',
        encoding="utf-8",
    )
    detected = detect_workspace_file(tmp_path)
    assert detected.name == "conda.toml"


@pytest.mark.parametrize(
    "filename, parser_type",
    [
        ("pixi.toml", PixiTomlParser),
        ("conda.toml", CondaTomlParser),
        ("pyproject.toml", PyprojectTomlParser),
    ],
    ids=["pixi", "conda", "pyproject"],
)
def test_find_parser(filename, parser_type):
    parser = find_parser(Path(filename))
    assert isinstance(parser, parser_type)


def test_find_parser_unknown():
    with pytest.raises(WorkspaceParseError, match="No parser"):
        find_parser(Path("setup.cfg"))


def test_detect_and_parse(sample_pixi_toml):
    _cached_parse.cache_clear()
    path, config = detect_and_parse(sample_pixi_toml.parent)
    assert path == sample_pixi_toml
    assert config.name == "test-project"


def test_detect_and_parse_not_found(tmp_path):
    with pytest.raises(WorkspaceNotFoundError):
        detect_and_parse(tmp_path)


def test_detect_defaults_to_cwd(sample_pixi_toml, monkeypatch):
    """detect_workspace_file(None) should use cwd."""
    monkeypatch.chdir(sample_pixi_toml.parent)
    path = detect_workspace_file(None)
    assert path == sample_pixi_toml


def test_detect_skips_file_without_workspace(tmp_path):
    """A pixi.toml without [workspace] should be skipped."""
    path = tmp_path / "pixi.toml"
    path.write_text('[dependencies]\npython = ">=3.10"\n', encoding="utf-8")
    with pytest.raises(WorkspaceNotFoundError):
        detect_workspace_file(tmp_path)
