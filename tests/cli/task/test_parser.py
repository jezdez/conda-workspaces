"""Tests for task CLI parser configuration."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from conda_workspaces.cli.main import execute_task, generate_task_parser


def test_returns_parser():
    assert isinstance(generate_task_parser(), argparse.ArgumentParser)


@pytest.mark.parametrize(
    ("argv", "expected_subcmd"),
    [
        (["list"], "list"),
        (["run", "build"], "run"),
        (["add", "mytask", "echo hello"], "add"),
        (["remove", "mytask"], "remove"),
        (["export"], "export"),
    ],
)
def test_subcommand_routing(argv, expected_subcmd):
    args = generate_task_parser().parse_args(argv)
    assert args.subcmd == expected_subcmd


@pytest.mark.parametrize(
    ("argv", "attr", "expected"),
    [
        (["run", "build"], "task_name", "build"),
        (["run", "test", "src/tests/"], "task_args", ["src/tests/"]),
        (["run", "build", "--skip-deps"], "skip_deps", True),
        (["run", "build", "--clean-env"], "clean_env", True),
        (
            ["add", "mytask", "echo hello", "--depends-on", "build"],
            "depends_on",
            ["build"],
        ),
        (["remove", "mytask"], "task_name", "mytask"),
        (["--file", "custom.yml", "list"], "file", Path("custom.yml")),
        (["export", "-o", "out.yml"], "output", Path("out.yml")),
    ],
)
def test_parser_args(argv, attr, expected):
    args = generate_task_parser().parse_args(argv)
    assert getattr(args, attr) == expected


def test_execute_no_subcmd_prints_help(capsys):
    args = argparse.Namespace(subcmd=None)
    result = execute_task(args)
    assert result == 0
    output = capsys.readouterr().out
    assert "task" in output or "usage" in output.lower()


def test_execute_unknown_subcmd_prints_help(capsys):
    args = argparse.Namespace(subcmd="unknown", file=None)
    result = execute_task(args)
    assert result == 0
    output = capsys.readouterr().out
    assert "task" in output or "usage" in output.lower()
