"""Environment exporter plugin for ``conda export --format=<lockfile>``.

Exports installed conda environments to ``conda.lock``.  Allows::

    conda export --format=conda-workspaces-lock-v1 --file=conda.lock
    conda export --format=conda-workspaces-lock --file=conda.lock \
        --platform=linux-64 --platform=osx-arm64

The exporter uses the same serialisation logic as the built-in
``conda workspace lock`` command, ensuring lockfile consistency
regardless of which code path produced the file.  Format metadata
(canonical name, aliases, default filename) is owned by
:mod:`.lockfile` so that the spec plugin, the exporter plugin and the
hand-written write path all agree.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

from conda.common.serialize.yaml import dump as yaml_dump
from conda_lockfiles.rattler_lock.v6 import _record_to_dict
from conda_lockfiles.validate_urls import validate_urls

from .lockfile import FORMAT, LOCKFILE_VERSION

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from conda.models.environment import Environment


def _envs_to_dict(envs: Iterable[Environment]) -> dict[str, Any]:
    """Build a lockfile dict from conda ``Environment`` objects."""
    seen_urls: set[str] = set()
    packages: list[dict[str, Any]] = []
    environments: dict[str, dict[str, Any]] = {}

    for env in envs:
        validate_urls(env, FORMAT)
        env_name = env.name or "default"
        platform = env.platform

        if env_name not in environments:
            environments[env_name] = {
                "channels": [{"url": ch} for ch in env.config.channels],
                "packages": {},
            }

        platform_refs: list[dict[str, str]] = []

        for pkg in sorted(env.explicit_packages, key=lambda p: p.name):
            platform_refs.append({"conda": pkg.url})
            if pkg.url not in seen_urls:
                packages.append(_record_to_dict(pkg))
                seen_urls.add(pkg.url)

        for manager, urls in env.external_packages.items():
            for url in urls:
                platform_refs.append({manager: url})

        environments[env_name]["packages"][platform] = platform_refs

    return {
        "version": LOCKFILE_VERSION,
        "environments": environments,
        "packages": packages,
    }


def multiplatform_export(envs: Iterable[Environment]) -> str:
    """Export ``Environment`` objects to a ``conda.lock`` YAML string.

    This function is registered as the ``multiplatform_export`` callable
    on the ``CondaEnvironmentExporter``.  conda calls it with one
    ``Environment`` per platform.
    """
    env_dict = _envs_to_dict(envs)
    buf = io.StringIO()
    yaml_dump(env_dict, buf)
    return buf.getvalue()
