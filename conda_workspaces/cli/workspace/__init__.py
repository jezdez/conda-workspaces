"""CLI subpackage for ``conda workspace`` subcommands."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...context import WorkspaceContext
from ...manifests import detect_and_parse

if TYPE_CHECKING:
    import argparse

    from ...models import WorkspaceConfig


def workspace_context_from_args(
    args: argparse.Namespace,
) -> tuple[WorkspaceConfig, WorkspaceContext]:
    """Parse the workspace manifest and build a context from CLI *args*.

    Uses ``--file`` / ``-f`` when provided, otherwise auto-detects.
    """
    manifest_path = getattr(args, "file", None)
    _, config = detect_and_parse(manifest_path)
    return config, WorkspaceContext(config)
