"""Tests for conda_workspaces.__main__ (``cw`` entry point)."""

from __future__ import annotations

import pytest

from conda_workspaces.__main__ import main


def test_main_no_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Calling main() with no arguments should print help and exit."""
    with pytest.raises(SystemExit):
        main([])


def test_main_sets_prog_to_cw(monkeypatch: pytest.MonkeyPatch) -> None:
    """Parser.prog should be 'cw', not 'conda workspace'."""
    captured_prog: list[str] = []

    class FakeParser:
        prog: str = ""

        def parse_args(self, args):
            captured_prog.append(self.prog)

            class NS:
                pass

            return NS()

    fake_parser = FakeParser()

    # main() does lazy imports from .cli.main, so patch there
    from conda_workspaces.cli import main as cli_main_mod

    monkeypatch.setattr(cli_main_mod, "generate_parser", lambda: fake_parser)
    monkeypatch.setattr(cli_main_mod, "execute", lambda parsed: 0)

    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == 0
    assert captured_prog == ["cw"]


@pytest.mark.parametrize(
    "exit_code",
    [0, 1, 42],
    ids=["success", "failure", "custom"],
)
def test_main_exits_with_execute_return_code(
    monkeypatch: pytest.MonkeyPatch, exit_code: int, tmp_path
) -> None:
    """main() should SystemExit with whatever execute() returns."""
    called_with: list = []

    class FakeParser:
        prog: str = ""

        def parse_args(self, args):
            class NS:
                pass

            return NS()

    fake_parser = FakeParser()

    # Patch the lazy imports within main()
    from conda_workspaces.cli import main as cli_main_mod

    monkeypatch.setattr(cli_main_mod, "generate_parser", lambda: fake_parser)
    monkeypatch.setattr(
        cli_main_mod, "execute", lambda parsed: exit_code
    )

    with pytest.raises(SystemExit) as exc_info:
        main([])

    assert exc_info.value.code == exit_code
