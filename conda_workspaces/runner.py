"""Shell execution backend for running task commands."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from conda.base.constants import on_win
from conda.base.context import context
from conda.utils import wrap_subprocess_call


class SubprocessShell:
    """Execute shell commands, optionally inside an activated conda env.

    When *conda_prefix* is given the command is executed inside an
    activated conda environment (mirroring ``conda run``).  Otherwise
    the command runs directly in the current shell.
    """

    def run(
        self,
        cmd: str | list[str],
        env: dict[str, str],
        cwd: Path,
        conda_prefix: Path | None = None,
        clean_env: bool = False,
    ) -> int:
        """Execute *cmd* and return the process exit code."""
        run_env = self._build_env(env, clean_env)

        if isinstance(cmd, list):
            cmd = " ".join(cmd)

        if conda_prefix is not None:
            return self._run_in_env(cmd, run_env, cwd, conda_prefix)
        return self._run_direct(cmd, run_env, cwd)

    def _build_env(self, extra: dict[str, str], clean: bool) -> dict[str, str]:
        """Build the environment variable mapping for a subprocess."""
        if clean:
            base: dict[str, str] = {}
            for key in (
                "PATH",
                "HOME",
                "USER",
                "LOGNAME",
                "SHELL",
                "TERM",
                "LANG",
                "SYSTEMROOT",
                "COMSPEC",
                "TEMP",
                "TMP",
            ):
                val = os.environ.get(key)
                if val is not None:
                    base[key] = val
        else:
            base = dict(os.environ)
        base.update(extra)
        return base

    def _run_direct(self, cmd: str, env: dict[str, str], cwd: Path) -> int:
        """Run *cmd* in the native shell without conda activation."""
        shell_cmd = self._shell_command(cmd)
        result = subprocess.run(shell_cmd, env=env, cwd=str(cwd))
        return result.returncode

    def _run_in_env(
        self,
        cmd: str,
        env: dict[str, str],
        cwd: Path,
        conda_prefix: Path,
    ) -> int:
        """Run *cmd* inside an activated conda environment at *conda_prefix*."""
        root_prefix = context.root_prefix
        dev_mode = context.dev
        debug_wrapper_scripts: bool = getattr(context, "debug_wrapper_scripts", False)

        script, command = wrap_subprocess_call(
            root_prefix,
            str(conda_prefix),
            dev_mode,
            debug_wrapper_scripts,
            self._shell_command(cmd),
        )
        try:
            result = subprocess.run(command, env=env, cwd=str(cwd))
            return result.returncode
        finally:
            if script and Path(script).exists():
                try:
                    Path(script).unlink()
                except OSError:
                    pass

    @staticmethod
    def _shell_command(cmd: str) -> list[str]:
        """Wrap *cmd* in the platform-appropriate shell invocation."""
        if on_win:
            return ["cmd", "/d", "/c", cmd]
        return [os.environ.get("SHELL", "/bin/sh"), "-c", cmd]
