"""Tests for ``conda task export``."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from conda_workspaces.cli.task.export import execute_export

if TYPE_CHECKING:
    from pathlib import Path
from conda_workspaces.parsers.toml import CondaTomlParser


def _export_args(file: Path, output: Path | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        file=file,
        output=output,
        quiet=False,
        verbose=0,
        json=False,
        dry_run=False,
    )


def test_export_to_stdout(sample_yaml, capsys):
    result = execute_export(_export_args(sample_yaml))
    assert result == 0
    output = capsys.readouterr().out
    assert "[tasks]" in output
    assert "build" in output
    assert "configure" in output


def test_export_to_file(sample_yaml, tmp_path):
    out_path = tmp_path / "exported.toml"
    result = execute_export(_export_args(sample_yaml, out_path))
    assert result == 0
    assert out_path.exists()

    tasks = CondaTomlParser().parse_tasks(out_path)
    assert "build" in tasks
    assert "test" in tasks
    assert "lint" in tasks


def test_export_from_pixi_toml(tmp_path):
    """Export from pixi.toml produces valid conda.toml."""
    pixi = tmp_path / "pixi.toml"
    pixi.write_text(
        '[tasks]\nbuild = "make build"\n'
        'test = { cmd = "pytest", depends-on = ["build"] }\n'
        "\n[target.win-64.tasks]\n"
        'build = "nmake build"\n'
    )

    out_path = tmp_path / "conda.toml"
    result = execute_export(_export_args(pixi, out_path))
    assert result == 0

    tasks = CondaTomlParser().parse_tasks(out_path)
    assert "build" in tasks
    assert "test" in tasks
    assert tasks["test"].depends_on[0].task == "build"
    assert tasks["build"].platforms is not None
    assert "win-64" in tasks["build"].platforms
