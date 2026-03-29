"""Tests for conda_workspaces.__main__ (``cw`` and ``ct`` entry points)."""

from __future__ import annotations

import pytest

from conda_workspaces.__main__ import main, main_task
from conda_workspaces.cli import main as cli_main_mod


class _FakeParser:
    prog: str = ""

    def __init__(self):
        self.captured_prog: list[str] = []

    def parse_args(self, args):
        self.captured_prog.append(self.prog)

        class NS:
            pass

        return NS()


def test_main_no_args_shows_help() -> None:
    with pytest.raises(SystemExit):
        main([])


def test_main_task_no_args_shows_help() -> None:
    with pytest.raises(SystemExit):
        main_task([])


def test_main_sets_prog_to_cw(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_parser = _FakeParser()

    monkeypatch.setattr(
        cli_main_mod, "generate_workspace_parser", lambda: fake_parser
    )
    monkeypatch.setattr(
        cli_main_mod, "execute_workspace", lambda parsed: 0
    )

    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 0
    assert fake_parser.captured_prog == ["cw"]


def test_main_task_sets_prog_to_ct(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_parser = _FakeParser()

    monkeypatch.setattr(
        cli_main_mod, "generate_task_parser", lambda: fake_parser
    )
    monkeypatch.setattr(
        cli_main_mod, "execute_task", lambda parsed: 0
    )

    with pytest.raises(SystemExit) as exc_info:
        main_task([])

    assert exc_info.value.code == 0
    assert fake_parser.captured_prog == ["ct"]


@pytest.mark.parametrize(
    "exit_code",
    [0, 1, 42],
    ids=["success", "failure", "custom"],
)
def test_main_exits_with_execute_return_code(
    monkeypatch: pytest.MonkeyPatch, exit_code: int
) -> None:
    fake_parser = _FakeParser()

    monkeypatch.setattr(
        cli_main_mod, "generate_workspace_parser", lambda: fake_parser
    )
    monkeypatch.setattr(
        cli_main_mod, "execute_workspace", lambda parsed: exit_code
    )

    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == exit_code
