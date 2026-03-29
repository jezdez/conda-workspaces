"""Tests for conda_workspaces.cli.workspace.add and workspace.remove."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import tomlkit

from conda_workspaces.cli.workspace.add import execute_add
from conda_workspaces.cli.workspace.remove import execute_remove

from ..conftest import make_args

if TYPE_CHECKING:
    from pathlib import Path

_DEFAULTS = {
    "file": None,
    "specs": [],
    "pypi": False,
    "feature": None,
    "environment": None,
}


@pytest.fixture
def pixi_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a pixi.toml and chdir to tmp_path."""
    content = """\
[workspace]
name = "add-test"
channels = ["conda-forge"]
platforms = ["linux-64"]

[dependencies]
python = ">=3.10"

[feature.test.dependencies]
pytest = ">=8.0"
"""
    path = tmp_path / "pixi.toml"
    path.write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return path


@pytest.fixture
def pyproject_toml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create a pyproject.toml with [tool.pixi] and chdir to tmp_path."""
    content = """\
[project]
name = "pp-test"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tool.pixi.dependencies]
python = ">=3.10"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return path


@pytest.mark.parametrize(
    "specs, expected_deps",
    [
        (["numpy"], {"numpy": "*"}),
        (["numpy >=1.24"], {"numpy": ">=1.24"}),
        (["numpy >=1.24", "pandas"], {"numpy": ">=1.24", "pandas": "*"}),
    ],
    ids=["bare-name", "with-version", "multiple"],
)
def test_add_conda_deps_to_pixi_toml(
    pixi_toml: Path, specs: list[str], expected_deps: dict[str, str]
) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=specs)
    result = execute_add(args)
    assert result == 0

    doc = tomlkit.loads(pixi_toml.read_text(encoding="utf-8"))
    for name, version in expected_deps.items():
        assert doc["dependencies"][name] == version


@pytest.mark.parametrize(
    "kwargs",
    [
        {"feature": "test"},
        {"environment": "test"},
    ],
    ids=["via-feature", "via-environment"],
)
def test_add_to_feature(pixi_toml: Path, kwargs: dict) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=["coverage"], **kwargs)
    execute_add(args)

    doc = tomlkit.loads(pixi_toml.read_text(encoding="utf-8"))
    assert doc["feature"]["test"]["dependencies"]["coverage"] == "*"


def test_add_pypi_deps(pixi_toml: Path) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=["requests >=2.0"], pypi=True)
    execute_add(args)

    doc = tomlkit.loads(pixi_toml.read_text(encoding="utf-8"))
    assert doc["pypi-dependencies"]["requests"] == ">=2.0"


def test_add_to_pyproject(pyproject_toml: Path) -> None:
    args = make_args(_DEFAULTS,file=pyproject_toml, specs=["numpy >=1.24"])
    execute_add(args)

    doc = tomlkit.loads(pyproject_toml.read_text(encoding="utf-8"))
    assert doc["tool"]["pixi"]["dependencies"]["numpy"] == ">=1.24"


@pytest.mark.parametrize(
    "specs, remaining",
    [
        (["python"], []),
        (["nonexistent"], ["python"]),
    ],
    ids=["remove-existing", "remove-missing-noop"],
)
def test_remove_from_pixi_toml(
    pixi_toml: Path, specs: list[str], remaining: list[str]
) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=specs)
    result = execute_remove(args)
    assert result == 0

    doc = tomlkit.loads(pixi_toml.read_text(encoding="utf-8"))
    actual = list(doc["dependencies"].keys())
    assert actual == remaining


def test_remove_from_feature(pixi_toml: Path) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=["pytest"], feature="test")
    execute_remove(args)

    doc = tomlkit.loads(pixi_toml.read_text(encoding="utf-8"))
    assert "pytest" not in doc["feature"]["test"]["dependencies"]


def test_remove_from_pyproject(pyproject_toml: Path) -> None:
    args = make_args(_DEFAULTS,file=pyproject_toml, specs=["python"])
    execute_remove(args)

    doc = tomlkit.loads(pyproject_toml.read_text(encoding="utf-8"))
    assert "python" not in doc["tool"]["pixi"]["dependencies"]


def test_remove_prints_no_match(
    pixi_toml: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=["nonexistent"])
    execute_remove(args)
    assert "No matching" in capsys.readouterr().out


def test_add_pypi_to_pyproject(pyproject_toml: Path) -> None:
    """Adding PyPI deps to pyproject.toml writes to pypi-dependencies."""
    args = make_args(_DEFAULTS,file=pyproject_toml, specs=["requests >=2.0"], pypi=True)
    execute_add(args)
    doc = tomlkit.loads(pyproject_toml.read_text(encoding="utf-8"))
    assert doc["tool"]["pixi"]["pypi-dependencies"]["requests"] == ">=2.0"


def test_add_to_pyproject_feature(pyproject_toml: Path) -> None:
    """Adding deps to a feature in pyproject.toml."""
    args = make_args(_DEFAULTS,file=pyproject_toml, specs=["pytest"], feature="test")
    execute_add(args)
    doc = tomlkit.loads(pyproject_toml.read_text(encoding="utf-8"))
    assert doc["tool"]["pixi"]["feature"]["test"]["dependencies"]["pytest"] == "*"


def test_remove_pypi_from_pyproject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Removing PyPI deps from pyproject.toml."""
    content = """\
[project]
name = "rm-pypi"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tool.pixi.pypi-dependencies]
requests = ">=2.0"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    args = make_args(_DEFAULTS,file=path, specs=["requests"], pypi=True)
    execute_remove(args)
    doc = tomlkit.loads(path.read_text(encoding="utf-8"))
    assert "requests" not in doc["tool"]["pixi"]["pypi-dependencies"]


def test_remove_from_pyproject_feature(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Removing deps from a feature in pyproject.toml."""
    content = """\
[project]
name = "rm-feat"

[tool.pixi.workspace]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tool.pixi.feature.test.dependencies]
pytest = ">=8.0"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    args = make_args(_DEFAULTS,file=path, specs=["pytest"], feature="test")
    execute_remove(args)
    doc = tomlkit.loads(path.read_text(encoding="utf-8"))
    assert "pytest" not in doc["tool"]["pixi"]["feature"]["test"]["dependencies"]


def test_remove_from_pyproject_no_table(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Removing from pyproject.toml with no tool table returns empty."""
    content = """\
[project]
name = "no-tool"
"""
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    args = make_args(_DEFAULTS,file=path, specs=["numpy"])
    result = execute_remove(args)
    assert result == 0
    assert "No matching" in capsys.readouterr().out


@pytest.mark.parametrize(
    "fixture_attr, root_keys",
    [
        ("pixi_toml", ()),
        ("pyproject_toml", ("tool", "pixi")),
    ],
    ids=["pixi-toml", "pyproject-toml"],
)
def test_add_environment_auto_creates_env_entry(
    fixture_attr: str,
    root_keys: tuple[str, ...],
    request: pytest.FixtureRequest,
) -> None:
    """Adding to an undefined environment auto-creates the env entry."""
    path = request.getfixturevalue(fixture_attr)
    args = make_args(_DEFAULTS,file=path, specs=["numpy"], environment="newenv")
    result = execute_add(args)
    assert result == 0

    doc = tomlkit.loads(path.read_text(encoding="utf-8"))
    root = doc
    for key in root_keys:
        root = root[key]
    assert root["feature"]["newenv"]["dependencies"]["numpy"] == "*"
    assert "newenv" in root["environments"]
    assert root["environments"]["newenv"]["features"] == ["newenv"]


def test_add_environment_existing_env_no_duplicate(pixi_toml: Path) -> None:
    """Adding to an existing feature+env doesn't duplicate the env entry."""
    args = make_args(_DEFAULTS,file=pixi_toml, specs=["coverage"], environment="test")
    execute_add(args)

    # First add auto-created the env entry. Add again — it shouldn't duplicate.
    args2 = make_args(
        _DEFAULTS, file=pixi_toml, specs=["hypothesis"], environment="test",
    )
    execute_add(args2)

    doc2 = tomlkit.loads(pixi_toml.read_text(encoding="utf-8"))
    assert doc2["feature"]["test"]["dependencies"]["hypothesis"] == "*"
    assert "test" in doc2["environments"]


@pytest.mark.parametrize(
    "specs, extra_kwargs, expected_text",
    [
        (["python"], {}, "default"),
        (["pytest"], {"feature": "test"}, "feature 'test'"),
    ],
    ids=["default", "feature"],
)
def test_remove_prints_location(
    pixi_toml: Path,
    capsys: pytest.CaptureFixture[str],
    specs: list[str],
    extra_kwargs: dict,
    expected_text: str,
) -> None:
    args = make_args(_DEFAULTS,file=pixi_toml, specs=specs, **extra_kwargs)
    execute_remove(args)
    out = capsys.readouterr().out
    assert expected_text in out
    assert "Removed 1" in out
