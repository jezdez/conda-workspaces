"""Tests for ``conda task run``."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

import conda_workspaces.cli.task.run as run_mod
from conda_workspaces.cli.task.run import _resolve_task_args, execute_run
from conda_workspaces.exceptions import CondaWorkspacesError, TaskExecutionError
from conda_workspaces.models import Task, TaskArg


def _run_args(
    task_file: Path, task_name: str = "greet", **overrides
) -> argparse.Namespace:
    """Build an argparse.Namespace suitable for execute_run."""
    defaults = dict(
        file=task_file,
        task_name=task_name,
        task_args=[],
        skip_deps=False,
        dry_run=False,
        quiet=False,
        verbose=0,
        clean_env=False,
        cwd=None,
        environment=None,
        templated=False,
        json=False,
    )
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


class FakeShell:
    """Test double for SubprocessShell that records calls."""

    def __init__(self, return_code: int = 0):
        self.calls: list[tuple] = []
        self.return_code = return_code

    def run(self, cmd, env, cwd, conda_prefix=None, clean_env=False):
        self.calls.append((cmd, env, cwd, conda_prefix, clean_env))
        return self.return_code


@pytest.mark.parametrize(
    ("args_def", "cli_args", "expected"),
    [
        ([], [], {}),
        ([TaskArg(name="path", default="tests/")], [], {"path": "tests/"}),
        ([TaskArg(name="path", default="tests/")], ["src/"], {"path": "src/"}),
        (
            [TaskArg(name="a"), TaskArg(name="b", default="y")],
            ["x"],
            {"a": "x", "b": "y"},
        ),
    ],
    ids=["no-args", "default", "override", "mixed"],
)
def test_resolve_task_args(args_def, cli_args, expected):
    task = Task(name="t", cmd="echo", args=args_def)
    assert _resolve_task_args(task, cli_args) == expected


def test_resolve_task_args_missing_required():
    task = Task(name="t", cmd="echo", args=[TaskArg(name="path")])
    with pytest.raises(CondaWorkspacesError, match="Missing required argument"):
        _resolve_task_args(task, [])


def test_execute_run_dry_run(tmp_path, capsys):
    """Dry-run should print commands without executing them."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text('[tasks]\ngreet = "echo hello"\n')

    result = execute_run(_run_args(task_file, dry_run=True))
    assert result == 0
    output = capsys.readouterr().out
    assert "[dry-run]" in output
    assert "greet" in output


def test_execute_run_dry_run_with_deps(tmp_path, capsys):
    """Dry-run prints all tasks in dependency order."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks]\nsetup = "echo setup"\n\n'
        '[tasks.build]\ncmd = "echo build"\ndepends-on = ["setup"]\n'
    )
    result = execute_run(_run_args(task_file, task_name="build", dry_run=True))
    assert result == 0
    output = capsys.readouterr().out
    assert "setup" in output
    assert "build" in output


def test_execute_run_dry_run_alias_done(tmp_path, capsys):
    """Alias tasks print [done] after their dependencies in dry-run."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks]\nlint = "ruff check ."\ntest = "pytest"\n\n'
        '[tasks.check]\ndepends-on = ["lint", "test"]\n'
    )

    result = execute_run(_run_args(task_file, task_name="check", dry_run=True))
    assert result == 0
    output = capsys.readouterr().out
    assert "[dry-run] lint" in output
    assert "[dry-run] test" in output
    assert "[done] check" in output


def test_execute_run_alias_done(tmp_path, capsys, monkeypatch):
    """Alias tasks print [done] after dependencies finish executing."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks]\nlint = "ruff check ."\ntest = "pytest"\n\n'
        '[tasks.check]\ndepends-on = ["lint", "test"]\n'
    )

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    result = execute_run(_run_args(task_file, task_name="check"))

    assert result == 0
    output = capsys.readouterr().out
    assert "[run] lint" in output
    assert "[run] test" in output
    assert "[done] check" in output


def test_execute_run_alias_quiet(tmp_path, capsys, monkeypatch):
    """Quiet mode suppresses [done] for alias tasks."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks]\nlint = "ruff check ."\n\n'
        '[tasks.check]\ndepends-on = ["lint"]\n'
    )

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    result = execute_run(_run_args(task_file, task_name="check", quiet=True))

    assert result == 0
    assert capsys.readouterr().out == ""


def test_execute_run_list_command(tmp_path, capsys):
    """List-form commands are joined for dry-run display."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks]\nbuild = "cmake --build ."\n'
    )

    result = execute_run(_run_args(task_file, task_name="build", dry_run=True))
    assert result == 0
    output = capsys.readouterr().out
    assert "cmake --build ." in output


def test_execute_run_real(tmp_path, capsys, monkeypatch):
    """Actual execution (fake shell) prints [run] and returns 0."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text('[tasks]\ngreet = "echo hello"\n')

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    result = execute_run(_run_args(task_file))

    assert result == 0
    output = capsys.readouterr().out
    assert "[run]" in output


def test_execute_run_quiet(tmp_path, capsys, monkeypatch):
    """Quiet mode suppresses output."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text('[tasks]\ngreet = "echo hello"\n')

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    result = execute_run(_run_args(task_file, quiet=True))

    assert result == 0
    assert capsys.readouterr().out == ""


def test_execute_run_failure(tmp_path, monkeypatch):
    """Non-zero exit raises TaskExecutionError."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text('[tasks]\nfail = "exit 1"\n')

    fake = FakeShell(return_code=1)
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    with pytest.raises(TaskExecutionError, match="fail"):
        execute_run(_run_args(task_file, task_name="fail"))


def test_execute_run_verbose_with_io(tmp_path, capsys, monkeypatch):
    """Verbose mode prints inputs/outputs."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks.build]\ncmd = "make"\ninputs = ["src/*.py"]\noutputs = ["dist/"]\n'
    )

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    monkeypatch.setattr(run_mod, "is_cached", lambda *a, **kw: False)
    result = execute_run(_run_args(task_file, task_name="build", verbose=1))

    assert result == 0
    output = capsys.readouterr().out
    assert "inputs:" in output
    assert "outputs:" in output


def test_execute_run_cached_skips(tmp_path, capsys, monkeypatch):
    """Cached tasks are skipped with [cached] message."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks.build]\ncmd = "make"\ninputs = ["src/*.py"]\noutputs = ["dist/"]\n'
    )

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    monkeypatch.setattr(run_mod, "is_cached", lambda *a, **kw: True)
    result = execute_run(_run_args(task_file, task_name="build"))

    assert result == 0
    output = capsys.readouterr().out
    assert "[cached]" in output


def test_execute_run_with_cwd_override(tmp_path, capsys, monkeypatch):
    """--cwd overrides the task's working directory."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text('[tasks]\ngreet = "echo hello"\n')
    subdir = tmp_path / "sub"
    subdir.mkdir()

    fake = FakeShell()
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    result = execute_run(_run_args(task_file, cwd=subdir))

    assert result == 0
    assert len(fake.calls) == 1
    assert Path(fake.calls[0][2]) == subdir


def test_execute_run_saves_cache(tmp_path, monkeypatch):
    """Successful run with inputs/outputs saves to cache."""
    task_file = tmp_path / "conda.toml"
    task_file.write_text(
        '[tasks.build]\ncmd = "make"\ninputs = ["src/*.py"]\noutputs = ["dist/"]\n'
    )

    fake = FakeShell()
    save_calls: list[tuple] = []
    monkeypatch.setattr(run_mod, "SubprocessShell", lambda: fake)
    monkeypatch.setattr(run_mod, "is_cached", lambda *a, **kw: False)
    monkeypatch.setattr(run_mod, "save_cache", lambda *a, **kw: save_calls.append(a))
    result = execute_run(_run_args(task_file, task_name="build", quiet=True))

    assert result == 0
    assert len(save_calls) == 1
