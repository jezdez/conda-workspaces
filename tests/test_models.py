"""Tests for conda_workspaces.models."""

from __future__ import annotations

import pytest

from conda_workspaces.models import (
    Channel,
    Environment,
    Feature,
    MatchSpec,
    PyPIDependency,
    WorkspaceConfig,
)


@pytest.mark.parametrize(
    "spec_str, expected_name, expected_version",
    [
        ("numpy >=1.24", "numpy", ">=1.24"),
        ("numpy", "numpy", None),
        ("python >=3.10,<4", "python", ">=3.10,<4"),
        ("scipy *", "scipy", "*"),
    ],
    ids=["with-version", "no-version", "compound-version", "wildcard"],
)
def test_matchspec(spec_str, expected_name, expected_version):
    ms = MatchSpec(spec_str)
    assert ms.name == expected_name
    if expected_version is None:
        assert ms.version is None
    else:
        assert str(ms.version) == expected_version


@pytest.mark.parametrize(
    "name, spec, expected",
    [
        ("requests", ">=2.28", "requests>=2.28"),
        ("requests", "", "requests"),
        ("flask", ">=2.0,<3", "flask>=2.0,<3"),
    ],
    ids=["with-spec", "no-spec", "compound-spec"],
)
def test_pypi_dep_str(name, spec, expected):
    dep = PyPIDependency(name=name, spec=spec) if spec else PyPIDependency(name=name)
    assert str(dep) == expected


@pytest.mark.parametrize(
    "value, expected_canonical",
    [
        ("conda-forge", "conda-forge"),
        ("bioconda", "bioconda"),
        ("https://my.server/channel", "https://my.server/channel"),
    ],
    ids=["short-name", "other-name", "full-url"],
)
def test_channel(value, expected_canonical):
    ch = Channel(value)
    assert ch.canonical_name == expected_canonical


@pytest.mark.parametrize(
    "name, expected_default",
    [
        ("default", True),
        ("test", False),
        ("docs", False),
    ],
    ids=["default", "test", "docs"],
)
def test_feature_is_default(name, expected_default):
    f = Feature(name=name)
    assert f.is_default is expected_default


@pytest.mark.parametrize(
    "name, features, solve_group, expected_default",
    [
        ("default", [], None, True),
        ("test", ["test"], "main", False),
        ("docs", ["docs"], None, False),
    ],
    ids=["default", "test-with-group", "docs"],
)
def test_environment(name, features, solve_group, expected_default):
    env = Environment(name=name, features=features, solve_group=solve_group)
    assert env.is_default is expected_default
    assert env.solve_group == solve_group


def test_config_post_init_creates_defaults():
    config = WorkspaceConfig()
    assert "default" in config.features
    assert "default" in config.environments


def test_config_get_environment(sample_config):
    env = sample_config.get_environment("test")
    assert env.name == "test"
    assert "test" in env.features


def test_config_get_environment_not_found(sample_config):
    from conda_workspaces.exceptions import EnvironmentNotFoundError

    with pytest.raises(EnvironmentNotFoundError):
        sample_config.get_environment("nonexistent")


@pytest.mark.parametrize(
    "env_name, expected_names",
    [
        ("default", ["default"]),
        ("test", ["default", "test"]),
    ],
    ids=["default-only", "test-inherits-default"],
)
def test_config_resolve_features(sample_config, env_name, expected_names):
    env = sample_config.environments[env_name]
    features = sample_config.resolve_features(env)
    names = [f.name for f in features]
    for name in expected_names:
        assert name in names
    assert len(features) == len(expected_names)


def test_config_resolve_features_no_default():
    config = WorkspaceConfig(
        features={
            "default": Feature(name="default"),
            "standalone": Feature(name="standalone"),
        },
        environments={
            "default": Environment(name="default"),
            "isolated": Environment(
                name="isolated",
                features=["standalone"],
                no_default_feature=True,
            ),
        },
    )
    env = config.environments["isolated"]
    features = config.resolve_features(env)
    names = [f.name for f in features]
    assert "default" not in names
    assert "standalone" in names


def test_config_merged_conda_dependencies(sample_config):
    env = sample_config.environments["test"]
    merged = sample_config.merged_conda_dependencies(env)
    assert "python" in merged  # from default
    assert "numpy" in merged  # from default
    assert "pytest" in merged  # from test feature


def test_config_merged_channels(sample_config):
    env = sample_config.environments["test"]
    channels = sample_config.merged_channels(env)
    assert len(channels) >= 1
    assert channels[0].canonical_name == "conda-forge"


def test_config_merged_channels_deduplication():
    feat_a = Feature(
        name="a", channels=[Channel("conda-forge")]
    )
    config = WorkspaceConfig(
        channels=[Channel("conda-forge")],
        features={"default": Feature(name="default"), "a": feat_a},
        environments={
            "default": Environment(name="default"),
            "env": Environment(name="env", features=["a"]),
        },
    )
    env = config.environments["env"]
    channels = config.merged_channels(env)
    canonical = [ch.canonical_name for ch in channels]
    assert canonical.count("conda-forge") == 1
