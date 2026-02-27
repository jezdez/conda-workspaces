"""Tests for conda_workspaces.plugin."""

from __future__ import annotations

import pytest

from conda_workspaces.plugin import (
    conda_environment_exporters,
    conda_environment_specifiers,
    conda_subcommands,
)


def test_conda_subcommands_yields_workspace() -> None:
    items = list(conda_subcommands())
    assert len(items) == 1
    sub = items[0]
    assert sub.name == "workspace"
    assert sub.summary
    assert callable(sub.action)
    assert callable(sub.configure_parser)


@pytest.mark.parametrize(
    "name, expected_cls_name",
    [
        ("conda-workspaces", "CondaWorkspaceSpec"),
        ("conda-workspaces-lock", "CondaLockSpec"),
    ],
)
def test_conda_environment_specifiers(name: str, expected_cls_name: str) -> None:
    items = {s.name: s for s in conda_environment_specifiers()}
    assert name in items
    assert items[name].environment_spec.__name__ == expected_cls_name


def test_conda_environment_specifiers_count() -> None:
    assert len(list(conda_environment_specifiers())) == 2


def test_conda_environment_exporters_yields_one() -> None:
    items = list(conda_environment_exporters())
    assert len(items) == 1
    exp = items[0]
    assert exp.name == "conda-workspaces-lock"
    assert exp.aliases == ("workspace-lock",)
    assert exp.default_filenames == ("conda.lock",)
    assert callable(exp.multiplatform_export)
