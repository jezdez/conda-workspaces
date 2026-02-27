"""Temporary script to write test files."""
import pathlib

# --- tests/test_plugin.py ---
pathlib.Path("tests/test_plugin.py").write_text('''\
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
        ("conda-workspace", "CondaWorkspaceSpec"),
        ("conda-workspace-lock", "CondaLockSpec"),
    ],
)
def test_conda_environment_specifiers(
    name: str, expected_cls_name: str
) -> None:
    items = {s.name: s for s in conda_environment_specifiers()}
    assert name in items
    assert items[name].environment_spec.__name__ == expected_cls_name


def test_conda_environment_specifiers_count() -> None:
    assert len(list(conda_environment_specifiers())) == 2


def test_conda_environment_exporters_yields_one() -> None:
    items = list(conda_environment_exporters())
    assert len(items) == 1
    exp = items[0]
    assert exp.name == "conda-workspace-lock"
    assert exp.aliases == ("workspace-lock",)
    assert exp.default_filenames == ("conda.lock",)
    assert callable(exp.multiplatform_export)
''')

print("test_plugin.py written")

# --- tests/test_envs.py (replace _install_pypi_deps section) ---
envs_path = pathlib.Path("tests/test_envs.py")
content = envs_path.read_text()

marker = "# ---------------------------------------------------------------------------\n# _install_pypi_deps\n# ---------------------------------------------------------------------------"
if marker in content:
    idx = content.index(marker)
    content = content[:idx]

content += '''\
# ---------------------------------------------------------------------------
# _install_pypi_deps
# ---------------------------------------------------------------------------


def test_install_pypi_deps_no_conda_pypi(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When conda-pypi is not installed, warns and returns."""
    import builtins
    import logging

    from conda_workspaces.envs import _install_pypi_deps
    from conda_workspaces.models import PyPIDependency
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(
        name="default",
        pypi_dependencies={
            "requests": PyPIDependency(name="requests"),
        },
    )

    real_import = builtins.__import__

    def _block_conda_pypi(name, *args, **kwargs):
        if name.startswith("conda_pypi"):
            raise ImportError("no conda-pypi")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _block_conda_pypi)

    with caplog.at_level(logging.WARNING):
        _install_pypi_deps(tmp_path, resolved)

    assert "conda-pypi is not installed" in caplog.text
    assert "requests" in caplog.text


def test_install_pypi_deps_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When conda-pypi is available, calls ConvertTree + run_conda_install."""
    import sys
    import types

    from conda_workspaces.envs import _install_pypi_deps
    from conda_workspaces.models import PyPIDependency
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(
        name="default",
        pypi_dependencies={
            "requests": PyPIDependency(name="requests", spec=">=2.28"),
        },
    )

    convert_calls: list[list] = []
    install_calls: list[dict] = []

    def fake_convert_tree_factory(prefix):
        repo = tmp_path / "conda-pypi-repo"
        repo.mkdir(exist_ok=True)

        class _ct:
            pass

        ct = _ct()
        ct.repo = repo

        def convert(specs):
            convert_calls.append(specs)

        ct.convert_tree = convert
        return ct

    def fake_run_conda_install(prefix, specs, **kwargs):
        install_calls.append({"prefix": prefix, "specs": specs, **kwargs})
        return 0

    # Wire up fake conda_pypi modules via sys.modules
    conda_pypi = types.ModuleType("conda_pypi")
    ct_mod = types.ModuleType("conda_pypi.convert_tree")
    ct_mod.ConvertTree = fake_convert_tree_factory
    main_mod = types.ModuleType("conda_pypi.main")
    main_mod.run_conda_install = fake_run_conda_install
    tr_mod = types.ModuleType("conda_pypi.translate")
    tr_mod.pypi_to_conda_name = lambda n: n.replace("-", "_")

    monkeypatch.setitem(sys.modules, "conda_pypi", conda_pypi)
    monkeypatch.setitem(sys.modules, "conda_pypi.convert_tree", ct_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.main", main_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.translate", tr_mod)

    _install_pypi_deps(tmp_path, resolved)

    assert len(convert_calls) == 1
    assert len(install_calls) == 1
    assert install_calls[0]["yes"] is True
    assert install_calls[0]["quiet"] is True


def test_install_pypi_deps_exception_warns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When convert_tree raises, logs warning and continues."""
    import logging
    import sys
    import types

    from conda_workspaces.envs import _install_pypi_deps
    from conda_workspaces.models import PyPIDependency
    from conda_workspaces.resolver import ResolvedEnvironment

    resolved = ResolvedEnvironment(
        name="default",
        pypi_dependencies={"flask": PyPIDependency(name="flask")},
    )

    def broken_factory(prefix):
        repo = tmp_path / "repo"
        repo.mkdir(exist_ok=True)

        class _ct:
            pass

        ct = _ct()
        ct.repo = repo

        def convert(specs):
            raise RuntimeError("download failed")

        ct.convert_tree = convert
        return ct

    conda_pypi = types.ModuleType("conda_pypi")
    ct_mod = types.ModuleType("conda_pypi.convert_tree")
    ct_mod.ConvertTree = broken_factory
    main_mod = types.ModuleType("conda_pypi.main")
    main_mod.run_conda_install = lambda *a, **kw: 0
    tr_mod = types.ModuleType("conda_pypi.translate")
    tr_mod.pypi_to_conda_name = lambda n: n

    monkeypatch.setitem(sys.modules, "conda_pypi", conda_pypi)
    monkeypatch.setitem(sys.modules, "conda_pypi.convert_tree", ct_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.main", main_mod)
    monkeypatch.setitem(sys.modules, "conda_pypi.translate", tr_mod)

    with caplog.at_level(logging.WARNING):
        _install_pypi_deps(tmp_path, resolved)

    assert "Failed to install PyPI dependencies" in caplog.text
    assert "flask" in caplog.text
'''

envs_path.write_text(content)
print("test_envs.py written")

# --- tests/test_lockfile.py (replace _urls_to_records section) ---
lock_path = pathlib.Path("tests/test_lockfile.py")
content = lock_path.read_text()

marker = "# ---------------------------------------------------------------------------\n# _urls_to_records\n# ---------------------------------------------------------------------------"
if marker in content:
    idx = content.index(marker)
    content = content[:idx]

content += '''\
# ---------------------------------------------------------------------------
# _urls_to_records
# ---------------------------------------------------------------------------


def test_urls_to_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """Converts URLs to records and enriches with lockfile metadata."""
    from conda_workspaces.lockfile import _urls_to_records

    urls = [
        "https://example.com/python-3.10.conda",
        "https://example.com/numpy-1.24.conda",
    ]
    lookup = {
        "https://example.com/python-3.10.conda": {
            "sha256": "aaa",
            "md5": "bbb",
        },
        "https://example.com/numpy-1.24.conda": {"sha256": "ccc"},
    }

    class _Rec:
        def __init__(self, url):
            self.url = url

    monkeypatch.setattr(
        "conda.misc.get_package_records_from_explicit",
        lambda url_list: [_Rec(u) for u in url_list],
    )

    records = _urls_to_records(urls, lookup)

    assert len(records) == 2
    assert records[0].url == "https://example.com/python-3.10.conda"
    assert records[0].sha256 == "aaa"
    assert records[0].md5 == "bbb"
    assert records[1].sha256 == "ccc"


def test_urls_to_records_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Handles empty URL lists."""
    from conda_workspaces.lockfile import _urls_to_records

    monkeypatch.setattr(
        "conda.misc.get_package_records_from_explicit",
        lambda urls: [],
    )

    assert _urls_to_records([], {}) == []


def test_urls_to_records_missing_lookup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Skips enrichment when URL not in lookup."""
    from conda_workspaces.lockfile import _urls_to_records

    class _Rec:
        def __init__(self, url):
            self.url = url

    monkeypatch.setattr(
        "conda.misc.get_package_records_from_explicit",
        lambda urls: [_Rec(u) for u in urls],
    )

    records = _urls_to_records(
        ["https://example.com/pkg.conda"],
        {},  # empty lookup
    )

    assert len(records) == 1
    assert not hasattr(records[0], "sha256")
'''

lock_path.write_text(content)
print("test_lockfile.py written")

print("All test files written successfully")
