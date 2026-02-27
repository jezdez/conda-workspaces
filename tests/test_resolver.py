"""Tests for conda_workspaces.resolver."""

from __future__ import annotations

import pytest

from conda_workspaces.exceptions import EnvironmentNotFoundError, PlatformError
from conda_workspaces.resolver import (
    group_by_solve_group,
    resolve_all_environments,
    resolve_environment,
)


@pytest.mark.parametrize(
    "env_name, expected_deps",
    [
        ("default", ["python", "numpy"]),
        ("test", ["python", "numpy", "pytest"]),
        ("docs", ["python", "numpy", "sphinx"]),
    ],
    ids=["default", "test-inherits-default", "docs-inherits-default"],
)
def test_resolve_dependencies(sample_config, env_name, expected_deps):
    resolved = resolve_environment(sample_config, env_name)
    assert resolved.name == env_name
    for dep in expected_deps:
        assert dep in resolved.conda_dependencies


def test_resolve_not_found(sample_config):
    with pytest.raises(EnvironmentNotFoundError):
        resolve_environment(sample_config, "nonexistent")


@pytest.mark.parametrize(
    "platform, should_raise",
    [
        ("linux-64", False),
        ("osx-arm64", False),
        ("win-64", False),
        ("linux-aarch64", True),
    ],
    ids=["linux-valid", "osx-valid", "win-valid", "aarch64-invalid"],
)
def test_resolve_platform_validation(sample_config, platform, should_raise):
    if should_raise:
        with pytest.raises(PlatformError):
            resolve_environment(sample_config, "default", platform=platform)
    else:
        resolved = resolve_environment(sample_config, "default", platform=platform)
        assert resolved.name == "default"


def test_resolve_channels(sample_config):
    resolved = resolve_environment(sample_config, "default")
    assert len(resolved.channels) >= 1
    assert resolved.channels[0].canonical_name == "conda-forge"


@pytest.mark.parametrize(
    "env_name, expected_group",
    [
        ("test", "default"),
        ("docs", None),
    ],
    ids=["with-group", "no-group"],
)
def test_resolve_solve_group(sample_config, env_name, expected_group):
    resolved = resolve_environment(sample_config, env_name)
    assert resolved.solve_group == expected_group


def test_resolve_all(sample_config):
    all_resolved = resolve_all_environments(sample_config)
    assert set(all_resolved) == {"default", "test", "docs"}


def test_group_by_solve_group(sample_config):
    all_resolved = resolve_all_environments(sample_config)
    groups = group_by_solve_group(all_resolved)

    # default and test share solve-group "default"
    assert "default" in groups
    names = [r.name for r in groups["default"]]
    assert "default" in names
    assert "test" in names

    # docs has no solve-group
    assert None in groups
    docs_names = [r.name for r in groups[None]]
    assert "docs" in docs_names
