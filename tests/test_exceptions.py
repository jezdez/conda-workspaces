"""Tests for conda_workspaces.exceptions."""

from __future__ import annotations

from pathlib import Path

import pytest

from conda_workspaces.exceptions import (
    ActivationError,
    ChannelError,
    CondaWorkspacesError,
    EnvironmentNotFoundError,
    EnvironmentNotInstalledError,
    FeatureNotFoundError,
    LockfileNotFoundError,
    ManifestExistsError,
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
        (
            ChannelError("bad channel config"),
            ["bad channel config"],
        ),
        (
            ActivationError("dev", "shell not found"),
            ["dev", "shell not found"],
        ),
        (
            LockfileNotFoundError("test", Path("conda.lock")),
            ["test", "conda.lock"],
        ),
        (
            EnvironmentNotInstalledError("dev"),
            ["dev", "not installed"],
        ),
        (
            ManifestExistsError("pixi.toml"),
            ["pixi.toml", "already exists"],
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
        "channel-error",
        "activation-error",
        "lockfile-not-found",
        "env-not-installed",
        "manifest-exists",
    ],
)
def test_exception_message(exc, expected_fragments):
    msg = str(exc)
    for fragment in expected_fragments:
        assert fragment in msg


def test_inheritance():
    from conda.exceptions import CondaError

    assert issubclass(CondaWorkspacesError, CondaError)


@pytest.mark.parametrize(
    "exc, attr, expected",
    [
        (ActivationError("dev", "shell not found"), "environment", "dev"),
        (LockfileNotFoundError("test", Path("conda.lock")), "environment", "test"),
    ],
    ids=["activation-env", "lockfile-env"],
)
def test_exception_attributes(exc, attr, expected):
    assert getattr(exc, attr) == expected
