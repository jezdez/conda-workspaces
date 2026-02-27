"""Tests for conda_workspaces.cli.main — parser configuration and dispatch."""

from __future__ import annotations

import argparse

import pytest

from conda_workspaces.cli.main import configure_parser, execute, generate_parser


def test_generate_parser_returns_parser() -> None:
    parser = generate_parser()
    assert isinstance(parser, argparse.ArgumentParser)
    assert "workspace" in parser.prog


@pytest.mark.parametrize(
    "subcmd",
    ["init", "install", "list", "info", "add", "remove", "clean", "run", "activate"],
)
def test_subcommands_registered(subcmd: str) -> None:
    parser = generate_parser()
    # Parsing a known subcommand should set args.subcmd
    # Use minimal valid args for each subcommand
    if subcmd == "add":
        args = parser.parse_args([subcmd, "numpy"])
    elif subcmd == "remove":
        args = parser.parse_args([subcmd, "numpy"])
    elif subcmd == "run":
        args = parser.parse_args([subcmd, "--", "echo", "hi"])
    else:
        args = parser.parse_args([subcmd])
    assert args.subcmd == subcmd


def test_no_subcmd_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    parser = generate_parser()
    args = parser.parse_args([])
    result = execute(args)
    assert result == 0
    captured = capsys.readouterr()
    assert "workspace" in captured.out.lower() or "usage" in captured.out.lower()


def test_unknown_subcmd_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    """An unrecognised subcmd falls through to the else branch."""
    parser = generate_parser()
    args = parser.parse_args([])
    args.subcmd = "nonexistent"
    result = execute(args)
    assert result == 0


@pytest.mark.parametrize(
    "args, expected_attr, expected_value",
    [
        (["init", "--format", "conda"], "manifest_format", "conda"),
        (["init", "--format", "pyproject"], "manifest_format", "pyproject"),
        (["init", "--name", "myproj"], "name", "myproj"),
        (["init", "-c", "defaults", "-c", "bioconda"], "channels", ["defaults", "bioconda"]),
        (["install", "-e", "test"], "environment", "test"),
        (["install", "--force-reinstall"], "force_reinstall", True),
        (["list", "--installed"], "installed", True),
        (["info", "test"], "env_name", "test"),
        (["info"], "env_name", "default"),
        (["add", "--pypi", "requests"], "pypi", True),
        (["add", "--feature", "dev", "numpy"], "feature", "dev"),
        (["remove", "--pypi", "requests"], "pypi", True),
        (["clean", "-e", "test"], "environment", "test"),
        (["run", "-e", "test", "--", "pytest"], "environment", "test"),
        (["activate", "docs"], "env_name", "docs"),
        (["activate"], "env_name", "default"),
    ],
    ids=[
        "init-format-conda",
        "init-format-pyproject",
        "init-name",
        "init-channels",
        "install-env",
        "install-force",
        "list-installed",
        "info-named",
        "info-default",
        "add-pypi",
        "add-feature",
        "remove-pypi",
        "clean-env",
        "run-env",
        "activate-named",
        "activate-default",
    ],
)
def test_parser_args(
    args: list[str], expected_attr: str, expected_value: object
) -> None:
    parser = generate_parser()
    parsed = parser.parse_args(args)
    assert getattr(parsed, expected_attr) == expected_value
