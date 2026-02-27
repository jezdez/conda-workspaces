"""Tests for conda_workspaces.context."""

from __future__ import annotations

from pathlib import Path

import pytest

from conda_workspaces.context import WorkspaceContext
from conda_workspaces.models import (
    Channel,
    Environment,
    Feature,
    WorkspaceConfig,
)


@pytest.fixture
def config(tmp_path: Path) -> WorkspaceConfig:
    """Minimal workspace config rooted in tmp_path."""
    return WorkspaceConfig(
        name="ctx-test",
        root=str(tmp_path),
        channels=[Channel("conda-forge")],
        platforms=["linux-64", "osx-arm64"],
        features={"default": Feature(name="default")},
        environments={"default": Environment(name="default")},
    )


def test_config_passthrough(config: WorkspaceConfig) -> None:
    ctx = WorkspaceContext(config)
    assert ctx.config is config


def test_root(config: WorkspaceConfig) -> None:
    ctx = WorkspaceContext(config)
    assert ctx.root == Path(config.root)


def test_envs_dir(config: WorkspaceConfig) -> None:
    ctx = WorkspaceContext(config)
    assert ctx.envs_dir == Path(config.root) / ".conda" / "envs"


def test_platform_cached(
    config: WorkspaceConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    """platform property lazily imports from conda and caches the result."""
    ctx = WorkspaceContext(config)

    # Inject a fake value into the cache to avoid a real conda import
    ctx._cache["platform"] = "linux-64"
    assert ctx.platform == "linux-64"

    # Second access returns the cached value (not re-evaluated)
    ctx._cache["platform"] = "osx-arm64"
    assert ctx.platform == "osx-arm64"


def test_root_prefix_cached(config: WorkspaceConfig) -> None:
    ctx = WorkspaceContext(config)
    ctx._cache["root_prefix"] = Path("/fake/root")
    assert ctx.root_prefix == Path("/fake/root")


@pytest.mark.parametrize(
    "platforms, cached_platform, expected",
    [
        (["linux-64", "osx-arm64"], "linux-64", True),
        (["linux-64", "osx-arm64"], "win-64", False),
        ([], "anything", True),
    ],
    ids=["supported", "unsupported", "empty-means-all"],
)
def test_is_platform_supported(
    tmp_path: Path, platforms: list[str], cached_platform: str, expected: bool
) -> None:
    config = WorkspaceConfig(
        name="test",
        root=str(tmp_path),
        platforms=platforms,
        features={"default": Feature(name="default")},
        environments={"default": Environment(name="default")},
    )
    ctx = WorkspaceContext(config)
    ctx._cache["platform"] = cached_platform
    assert ctx.is_platform_supported is expected


@pytest.mark.parametrize(
    "env_name",
    ["default", "test", "docs"],
    ids=["default", "named-test", "named-docs"],
)
def test_env_prefix(config: WorkspaceConfig, env_name: str) -> None:
    ctx = WorkspaceContext(config)
    prefix = ctx.env_prefix(env_name)
    assert prefix == ctx.envs_dir / env_name


@pytest.mark.parametrize(
    "has_conda_meta, expected",
    [
        (True, True),
        (False, False),
    ],
    ids=["exists", "missing"],
)
def test_env_exists(
    config: WorkspaceConfig, has_conda_meta: bool, expected: bool
) -> None:
    ctx = WorkspaceContext(config)
    prefix = ctx.env_prefix("default")
    if has_conda_meta:
        (prefix / "conda-meta").mkdir(parents=True)
        (prefix / "conda-meta" / "history").write_text("", encoding="utf-8")
    assert ctx.env_exists("default") is expected
