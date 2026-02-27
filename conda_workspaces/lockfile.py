"""Lockfile generation and consumption for reproducible environments.

Produces a single ``conda.lock`` at the workspace root.  The file
captures all environments and platforms so that installations can be
reproduced exactly without running the solver.

The format is a YAML document with three top-level keys::

    version: 1
    environments:
      <name>:
        channels: [{url: ...}, ...]
        packages:
          <platform>: [{conda: <url>}, ...]
    packages:
      - conda: <url>
        sha256: ...
        md5: ...
        depends: [...]
        ...

On the *write* side, ``generate_lockfile`` snapshots every installed
environment.  On the *read* side, ``install_from_lockfile`` extracts
the package list for one environment + platform and installs the exact
URLs, bypassing the solver entirely.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from conda.common.serialize.yaml import dump as yaml_dump
from conda.common.serialize.yaml import load as yaml_load
from conda.models.environment import Environment
from conda_lockfiles.rattler_lock.v6 import _record_to_dict

from .exceptions import LockfileNotFoundError

if TYPE_CHECKING:
    from typing import Any

    from .context import WorkspaceContext

#: Lockfile format version.
LOCKFILE_VERSION = 1

#: The canonical lockfile filename.
LOCKFILE_NAME = "conda.lock"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def lockfile_path(ctx: WorkspaceContext) -> Path:
    """Return the path to the workspace lockfile (``<root>/conda.lock``)."""
    return ctx.root / LOCKFILE_NAME


def lockfile_exists(ctx: WorkspaceContext) -> bool:
    """Check whether a lockfile exists for the workspace."""
    return lockfile_path(ctx).is_file()


# ---------------------------------------------------------------------------
# Generating the lockfile
# ---------------------------------------------------------------------------


def _build_lockfile_dict(
    environments: dict[str, Environment],
    channels_by_env: dict[str, list[str]],
) -> dict[str, Any]:
    """Build the lockfile dict from a set of Environment objects.

    *environments* maps ``(env_name, platform)`` pairs to
    :class:`~conda.models.environment.Environment` objects — each
    entry represents one environment on one platform.

    *channels_by_env* maps environment names to ordered channel URLs.
    """
    seen_urls: set[str] = set()
    packages: list[dict[str, Any]] = []
    envs_dict: dict[str, dict[str, Any]] = {}

    for (env_name, platform), env in sorted(environments.items()):
        # Per-environment entry
        if env_name not in envs_dict:
            channels = channels_by_env.get(env_name, [])
            envs_dict[env_name] = {
                "channels": [{"url": ch} for ch in channels],
                "packages": {},
            }

        # Per-platform package references
        platform_refs: list[dict[str, str]] = []
        for pkg in sorted(env.explicit_packages, key=lambda p: p.name):
            platform_refs.append({"conda": pkg.url})
            if pkg.url not in seen_urls:
                packages.append(_record_to_dict(pkg))
                seen_urls.add(pkg.url)

        envs_dict[env_name]["packages"][platform] = platform_refs

    return {
        "version": LOCKFILE_VERSION,
        "environments": envs_dict,
        "packages": packages,
    }


def generate_lockfile(
    ctx: WorkspaceContext,
    env_names: list[str] | None = None,
) -> Path:
    """Generate a ``conda.lock`` from installed workspace environments.

    Snapshots every installed environment (or only *env_names* when
    given) into a single ``conda.lock`` YAML file at the workspace
    root.

    Returns the path to the generated lockfile.
    """
    if env_names is None:
        env_names = [name for name in ctx.config.environments if ctx.env_exists(name)]

    platform = ctx.platform
    environments: dict[tuple[str, str], Environment] = {}
    channels_by_env: dict[str, list[str]] = {}

    for name in env_names:
        prefix = ctx.env_prefix(name)
        env = Environment.from_prefix(
            prefix=str(prefix),
            name=name,
            platform=platform,
        )
        environments[(name, platform)] = env

        # Resolve channels from workspace config
        channels_by_env[name] = [str(ch) for ch in ctx.config.channels]

    data = _build_lockfile_dict(environments, channels_by_env)

    path = lockfile_path(ctx)
    with path.open("w", encoding="utf-8") as fh:
        yaml_dump(data, fh)
    return path


# ---------------------------------------------------------------------------
# Reading the lockfile
# ---------------------------------------------------------------------------


def _read_lockfile_data(ctx: WorkspaceContext) -> dict[str, Any]:
    """Parse ``conda.lock`` and return the raw dict."""
    path = lockfile_path(ctx)
    if not path.is_file():
        raise LockfileNotFoundError("(all)", path)
    with path.open() as fh:
        return yaml_load(fh)


def _extract_env_packages(
    data: dict[str, Any],
    env_name: str,
    platform: str,
) -> list[tuple[str, dict[str, Any]]]:
    """Return ``(url, metadata)`` pairs for an env+platform from lockfile data.

    Raises ``LockfileNotFoundError`` if the environment or platform is
    missing.
    """
    environments = data.get("environments", {})
    if env_name not in environments:
        raise LockfileNotFoundError(
            env_name,
            Path(LOCKFILE_NAME),
        )

    env_data = environments[env_name]
    platform_pkgs = env_data.get("packages", {}).get(platform)
    if platform_pkgs is None:
        raise LockfileNotFoundError(
            env_name,
            Path(LOCKFILE_NAME),
        )

    # Build a lookup from the top-level packages list
    all_packages = data.get("packages", [])
    lookup: dict[str, dict[str, Any]] = {}
    for pkg in all_packages:
        url = pkg.get("conda")
        if url:
            lookup[url] = pkg

    # Match platform references against the packages list
    result: list[tuple[str, dict[str, Any]]] = []
    for ref in platform_pkgs:
        url = ref.get("conda", "")
        metadata = lookup.get(url, {})
        result.append((url, metadata))

    return result


# ---------------------------------------------------------------------------
# Installing from the lockfile
# ---------------------------------------------------------------------------


def install_from_lockfile(ctx: WorkspaceContext, env_name: str) -> None:
    """Install an environment from ``conda.lock``.

    Reads the lockfile, extracts the package list for *env_name* on
    the current platform, downloads the exact packages, and installs
    them into the environment prefix — bypassing the solver entirely.

    Raises ``LockfileNotFoundError`` if the lockfile is missing or
    does not contain the requested environment/platform.
    """
    from conda.misc import (
        get_package_records_from_explicit,
        install_explicit_packages,
    )

    data = _read_lockfile_data(ctx)
    pkg_pairs = _extract_env_packages(data, env_name, ctx.platform)

    urls = [url for url, _meta in pkg_pairs]

    prefix = ctx.env_prefix(env_name)
    prefix.mkdir(parents=True, exist_ok=True)

    records = get_package_records_from_explicit(urls)
    install_explicit_packages(
        package_cache_records=list(records),
        prefix=str(prefix),
    )
