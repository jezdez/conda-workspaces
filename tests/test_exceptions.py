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
