"""Tests for conda_workspaces.template."""

from __future__ import annotations

import pytest
from conda.base.constants import on_win
from conda.base.context import context

from conda_workspaces.template import render, render_list


def test_render_no_template_fast_path():
    assert render("echo hello") == "echo hello"


def test_render_simple_variable():
    result = render("echo {{ greeting }}", task_args={"greeting": "hi"})
    assert result == "echo hi"


@pytest.mark.parametrize(
    "template",
    [
        "{% if conda.is_unix %}unix{% else %}win{% endif %}",
        "{% if pixi.is_unix %}unix{% else %}win{% endif %}",
    ],
    ids=["conda-namespace", "pixi-alias"],
)
def test_render_platform_conditional(template):
    result = render(template)
    expected = "win" if on_win else "unix"
    assert result == expected


def test_render_manifest_path(tmp_path):
    p = tmp_path / "conda.toml"
    result = render("{{ conda.manifest_path }}", manifest_path=p)
    assert result == str(p)


def test_render_platform_variable():
    assert render("{{ conda.platform }}") == context.subdir


def test_render_extra_context():
    """extra_context merges user-supplied variables into the template context."""
    result = render("{{ custom_var }}", extra_context={"custom_var": "hello"})
    assert result == "hello"


@pytest.mark.parametrize(
    ("items", "task_args", "expected"),
    [
        (
            ["src/{{ name }}.py", "tests/"],
            {"name": "main"},
            ["src/main.py", "tests/"],
        ),
        ([], {}, []),
    ],
    ids=["with-vars", "empty"],
)
def test_render_list(items, task_args, expected):
    assert render_list(items, task_args=task_args) == expected
