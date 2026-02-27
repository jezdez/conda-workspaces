"""Tests for conda_workspaces.env_spec."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

import conda_workspaces.env_spec as env_spec_mod
from conda_workspaces.env_spec import (
    LOCK_FILENAMES,
    WORKSPACE_FILENAMES,
    CondaLockSpec,
    CondaWorkspaceSpec,
)


class _FakeContext:
    """Lightweight stand-in for conda's context with a settable subdir."""

    def __init__(self, subdir: str = "linux-64"):
        self.subdir = subdir


@pytest.fixture(autouse=True)
def _patch_context(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Replace ``context`` inside env_spec with a fake set to linux-64.
    Autouse ensures this applies to all tests in this module.
    """
    monkeypatch.setattr(env_spec_mod, "context", _FakeContext("linux-64"))


@pytest.mark.parametrize(
    ("filename", "content", "expected"),
    [
        (
            "conda.toml",
            '[workspace]\nname = "test"\nchannels = ["conda-forge"]\n'
            'platforms = ["linux-64"]\n',
            True,
        ),
        ("pixi.toml", '[workspace]\nname = "x"\n', False),
        ("conda.toml", '[project]\nname = "x"\n', False),
        ("conda.toml", "not valid toml [[[", False),
    ],
)
def test_conda_workspace_spec_can_handle(
    tmp_path: Path, filename: str, content: str, expected: bool
) -> None:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    assert CondaWorkspaceSpec(path).can_handle() is expected


def test_conda_workspace_spec_can_handle_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "conda.toml"
    assert CondaWorkspaceSpec(path).can_handle() is False


def test_conda_workspace_spec_env_returns_environment(tmp_path: Path) -> None:
    """env property parses manifest and returns an Environment."""
    path = tmp_path / "conda.toml"
    path.write_text(
        '[workspace]\nname = "myproj"\nchannels = ["conda-forge"]\n'
        'platforms = ["linux-64"]\n\n'
        "[dependencies]\n"
        'python = ">=3.10"\n',
        encoding="utf-8",
    )

    spec = CondaWorkspaceSpec(path)
    env = spec.env

    assert env.name == "myproj"
    assert env.platform == "linux-64"
    assert len(env.requested_packages) == 1
    assert env.requested_packages[0].name == "python"
    assert "conda-forge" in env.config.channels


def test_conda_workspace_spec_env_pypi_deps_as_external(tmp_path: Path) -> None:
    """PyPI dependencies appear as external_packages under 'pip'."""
    path = tmp_path / "conda.toml"
    path.write_text(
        '[workspace]\nname = "proj"\nchannels = ["conda-forge"]\n'
        'platforms = ["linux-64"]\n\n'
        "[dependencies]\n"
        'python = ">=3.10"\n\n'
        "[pypi-dependencies]\n"
        'requests = "*"\n',
        encoding="utf-8",
    )

    spec = CondaWorkspaceSpec(path)
    env = spec.env

    assert "pip" in env.external_packages
    assert len(env.external_packages["pip"]) == 1


def test_conda_workspace_spec_env_name_fallback_to_dirname(
    tmp_path: Path,
) -> None:
    """When workspace has no name, falls back to parent directory."""
    path = tmp_path / "conda.toml"
    path.write_text(
        '[workspace]\nchannels = ["conda-forge"]\n'
        'platforms = ["linux-64"]\n\n'
        "[dependencies]\n"
        'python = ">=3.10"\n',
        encoding="utf-8",
    )

    spec = CondaWorkspaceSpec(path)
    env = spec.env
    assert env.name == tmp_path.name


@pytest.mark.parametrize(
    ("filename", "content", "expected"),
    [
        (
            "conda.lock",
            "version: 1\nenvironments: {}\npackages: []\n",
            True,
        ),
        ("pixi.lock", "version: 1\n", False),
        ("conda.lock", "version: 5\n", False),
        ("conda.lock", "{{not yaml::", False),
    ],
)
def test_conda_lock_spec_can_handle(
    tmp_path: Path, filename: str, content: str, expected: bool
) -> None:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    assert CondaLockSpec(path).can_handle() is expected


def test_conda_lock_spec_can_handle_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "conda.lock"
    assert CondaLockSpec(path).can_handle() is False


def test_conda_lock_spec_can_handle_caches_result(tmp_path: Path) -> None:
    """Second call to can_handle reuses cached data."""
    path = tmp_path / "conda.lock"
    content = "version: 1\nenvironments: {}\npackages: []\n"
    path.write_text(content, encoding="utf-8")
    spec = CondaLockSpec(path)
    assert spec.can_handle() is True
    assert spec._data_cache is not None
    # Overwrite file — cached data should still be used
    path.write_text("version: 99\n", encoding="utf-8")
    assert spec.can_handle() is True  # still cached


@pytest.fixture
def lockfile_content() -> str:
    return (
        "version: 1\n"
        "environments:\n"
        "  default:\n"
        "    channels:\n"
        "    - url: https://conda.anaconda.org/conda-forge\n"
        "    packages:\n"
        "      linux-64:\n"
        "      - conda: https://example.com/python-3.10.conda\n"
        "      - pypi: https://pypi.org/simple/requests/\n"
        "packages:\n"
        "- conda: https://example.com/python-3.10.conda\n"
        "  sha256: abc123\n"
    )


def test_conda_lock_spec_env_returns_explicit_packages(
    tmp_path: Path,
    lockfile_content: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "conda.lock"
    path.write_text(lockfile_content, encoding="utf-8")

    # Stub records_from_conda_urls to avoid real conda I/O
    class FakeRecord:
        def __init__(self, url: str):
            self.url = url
            self.name = "python"

    def fake_records_from_conda_urls(metadata_by_url, **kwargs):
        return tuple(FakeRecord(url) for url in metadata_by_url)

    monkeypatch.setattr(
        "conda_lockfiles.records_from_conda_urls.records_from_conda_urls",
        fake_records_from_conda_urls,
    )

    spec = CondaLockSpec(path)
    env = spec.env

    assert env.name == "default"
    assert env.platform == "linux-64"
    assert len(env.explicit_packages) == 1
    assert env.explicit_packages[0].url == "https://example.com/python-3.10.conda"


def test_conda_lock_spec_env_includes_pypi_external(
    tmp_path: Path,
    lockfile_content: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "conda.lock"
    path.write_text(lockfile_content, encoding="utf-8")

    def fake_records_from_conda_urls(metadata_by_url, **kwargs):
        return ()

    monkeypatch.setattr(
        "conda_lockfiles.records_from_conda_urls.records_from_conda_urls",
        fake_records_from_conda_urls,
    )

    spec = CondaLockSpec(path)
    env = spec.env

    assert "pip" in env.external_packages
    assert "https://pypi.org/simple/requests/" in env.external_packages["pip"]


def test_conda_lock_spec_env_missing_environment(tmp_path: Path) -> None:
    path = tmp_path / "conda.lock"
    path.write_text(
        "version: 1\nenvironments:\n  test: {}\npackages: []\n",
        encoding="utf-8",
    )
    spec = CondaLockSpec(path)
    with pytest.raises(ValueError, match="not found in lockfile"):
        spec.env


def test_conda_lock_spec_env_missing_platform(tmp_path: Path) -> None:
    path = tmp_path / "conda.lock"
    path.write_text(
        "version: 1\n"
        "environments:\n"
        "  default:\n"
        "    channels: []\n"
        "    packages:\n"
        "      osx-arm64: []\n"
        "packages: []\n",
        encoding="utf-8",
    )
    spec = CondaLockSpec(path)
    with pytest.raises(ValueError, match="does not list packages for platform"):
        spec.env


def test_conda_lock_spec_env_wrong_version_raises(tmp_path: Path) -> None:
    path = tmp_path / "conda.lock"
    content = "version: 99\nenvironments: {}\npackages: []\n"
    path.write_text(content, encoding="utf-8")
    # Bypass can_handle by pre-loading _data_cache
    spec = CondaLockSpec(path)
    spec._data_cache = {"version": 99, "environments": {}, "packages": []}
    with pytest.raises(ValueError, match="Unsupported lockfile version"):
        spec.env


def test_workspace_filenames() -> None:
    assert WORKSPACE_FILENAMES == {"conda.toml"}


def test_lock_filenames() -> None:
    assert LOCK_FILENAMES == {"conda.lock"}
