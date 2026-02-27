"""Tests for conda_workspaces.exceptions."""

from __future__ import annotations

import pytest

from conda_workspaces.exceptions import (
    CondaWorkspacesError,
    EnvironmentNotFoundError,
    FeatureNotFoundError,
    PlatformError,
    SolveError,
    WorkspaceNotFoundError,
    WorkspaceParseError,
)


@pytest.mark.parametrize(
    "exc, expected_fragments",
    [
        (
            WorkspaceNotFoundError("/some/dir"),
            ["/some/dir"],
        ),
        (
            WorkspaceParseError("/path/pixi.toml", "bad syntax"),
            ["pixi.toml", "bad syntax"],
        ),
        (
            EnvironmentNotFoundError("dev", ["default", "test"]),
            ["dev", "default", "test"],
        ),
        (
            EnvironmentNotFoundError("dev", []),
            ["dev"],
        ),
        (
            FeatureNotFoundError("gpu", "train"),
            ["gpu", "train"],
        ),
        (
            PlatformError("win-arm64", ["linux-64", "osx-arm64"]),
            ["win-arm64"],
        ),
        (
            SolveError("test", "conflict"),
            ["test"],
        ),
    ],
    ids=[
        "workspace-not-found",
        "parse-error",
        "env-not-found-with-available",
        "env-not-found-empty",
        "feature-not-found",
        "platform-error",
        "solve-error",
    ],
)
def test_exception_message(exc, expected_fragments):
    msg = str(exc)
    for fragment in expected_fragments:
        assert fragment in msg


def test_inheritance():
    from conda.exceptions import CondaError

    assert issubclass(CondaWorkspacesError, CondaError)


def test_channel_error():
    from conda_workspaces.exceptions import ChannelError

    exc = ChannelError("bad channel config")
    assert "bad channel config" in str(exc)


def test_activation_error():
    from conda_workspaces.exceptions import ActivationError

    exc = ActivationError("dev", "shell not found")
    assert "dev" in str(exc)
    assert "shell not found" in str(exc)
    assert exc.environment == "dev"


def test_lockfile_not_found_error():
    from pathlib import Path

    from conda_workspaces.exceptions import LockfileNotFoundError

    exc = LockfileNotFoundError("test", Path("conda.lock"))
    assert "test" in str(exc)
    assert "conda.lock" in str(exc)
    assert exc.environment == "test"


def test_environment_not_installed_error():
    from conda_workspaces.exceptions import EnvironmentNotInstalledError

    exc = EnvironmentNotInstalledError("dev")
    assert "dev" in str(exc)
    assert "not installed" in str(exc)


def test_manifest_exists_error():
    from conda_workspaces.exceptions import ManifestExistsError

    exc = ManifestExistsError("pixi.toml")
    assert "pixi.toml" in str(exc)
    assert "already exists" in str(exc)
