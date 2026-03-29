"""Tests for conda_workspaces.parsers.normalize."""

from __future__ import annotations

import pytest

from conda_workspaces.parsers.normalize import (
    normalize_args,
    normalize_depends_on,
    normalize_override,
    normalize_task,
)


@pytest.mark.parametrize(
    ("raw", "expected_tasks"),
    [
        (None, []),
        ("single", ["single"]),
        (["a", "b"], ["a", "b"]),
        ([{"task": "x", "args": ["1"], "environment": "py311"}], ["x"]),
    ],
    ids=["none", "string", "list-of-str", "dict-form"],
)
def test_normalize_depends_on(raw, expected_tasks):
    result = normalize_depends_on(raw)
    assert [d.task for d in result] == expected_tasks


def test_normalize_depends_on_dict_args():
    raw = [{"task": "x", "args": ["1"], "environment": "py311"}]
    result = normalize_depends_on(raw)
    assert result[0].args == ["1"]
    assert result[0].environment == "py311"


@pytest.mark.parametrize(
    ("raw", "expected_names"),
    [
        (None, []),
        (["name1"], ["name1"]),
        ([{"arg": "path", "default": "/tmp"}], ["path"]),
    ],
    ids=["none", "string-form", "dict-form"],
)
def test_normalize_args(raw, expected_names):
    result = normalize_args(raw)
    assert [a.name for a in result] == expected_names


def test_normalize_args_dict_default():
    result = normalize_args([{"arg": "path", "default": "/tmp"}])
    assert result[0].default == "/tmp"


def test_normalize_override_with_fields():
    raw = {
        "cmd": "make",
        "cwd": "/build",
        "env": {"CC": "gcc"},
        "inputs": ["*.c"],
        "outputs": ["*.o"],
        "clean-env": True,
    }
    ov = normalize_override(raw)
    assert ov.cmd == "make"
    assert ov.cwd == "/build"
    assert ov.env == {"CC": "gcc"}
    assert ov.inputs == ["*.c"]
    assert ov.outputs == ["*.o"]
    assert ov.clean_env is True


def test_normalize_task_list_form():
    """List-form creates an alias task with depends_on."""
    task = normalize_task("alias", ["dep1", "dep2"])
    assert task.cmd is None
    assert task.is_alias
    assert [d.task for d in task.depends_on] == ["dep1", "dep2"]


def test_normalize_task_with_target():
    raw = {
        "cmd": "make",
        "target": {
            "win-64": {"cmd": "nmake"},
        },
    }
    task = normalize_task("build", raw)
    assert task.platforms is not None
    assert "win-64" in task.platforms
    assert task.platforms["win-64"].cmd == "nmake"


def test_normalize_task_full_dict():
    raw = {
        "cmd": "pytest",
        "depends-on": ["build"],
        "env": {"X": "1"},
        "clean-env": True,
        "default-environment": "test",
        "cwd": "/src",
        "description": "Run tests",
        "inputs": ["*.py"],
        "outputs": ["results/"],
        "args": [{"arg": "path", "default": "tests/"}],
    }
    task = normalize_task("test", raw)
    assert task.cmd == "pytest"
    assert task.depends_on[0].task == "build"
    assert task.env == {"X": "1"}
    assert task.clean_env is True
    assert task.default_environment == "test"
    assert task.cwd == "/src"
    assert task.description == "Run tests"
    assert task.inputs == ["*.py"]
    assert task.outputs == ["results/"]
    assert task.args[0].name == "path"
    assert task.args[0].default == "tests/"
