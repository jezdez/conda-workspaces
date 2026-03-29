"""Shared logic for normalizing raw task dicts into Task model objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..exceptions import TaskParseError
from ..models import Task, TaskArg, TaskDependency, TaskOverride

if TYPE_CHECKING:
    from typing import Any


def normalize_depends_on(raw: list[Any] | str | None) -> list[TaskDependency]:
    """Convert the various ``depends-on`` formats into TaskDependency objects.

    Accepted shapes:
    - ``["foo", "bar"]``  (simple list of task names)
    - ``[{"task": "foo", "args": ["x"]}, ...]``  (full dict form)
    - ``[{"task": "foo"}, {"task": "bar"}]``  (pixi alias shorthand)
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        return [TaskDependency(task=raw)]
    result: list[TaskDependency] = []
    for item in raw:
        if isinstance(item, str):
            result.append(TaskDependency(task=item))
        elif isinstance(item, dict):
            result.append(
                TaskDependency(
                    task=item["task"],
                    args=item.get("args", []),
                    environment=item.get("environment"),
                )
            )
    return result


def normalize_args(raw: list[Any] | None) -> list[TaskArg]:
    """Convert raw arg definitions into TaskArg objects.

    Accepted shapes:
    - ``["name"]``  (required arg, no default)
    - ``[{"arg": "name", "default": "value"}]``
    - ``[{"arg": "name", "default": "value", "choices": ["a", "b"]}]``
    """
    if raw is None:
        return []
    result: list[TaskArg] = []
    for item in raw:
        if isinstance(item, str):
            result.append(TaskArg(name=item))
        elif isinstance(item, dict):
            result.append(
                TaskArg(
                    name=item["arg"],
                    default=item.get("default"),
                    choices=item.get("choices"),
                )
            )
    return result


def normalize_override(raw: dict[str, Any]) -> TaskOverride:
    """Parse a raw dict into a TaskOverride."""
    cmd = raw.get("cmd")
    return TaskOverride(
        cmd=cmd,
        args=normalize_args(raw.get("args")) or None,
        depends_on=normalize_depends_on(raw.get("depends-on", raw.get("depends_on")))
        or None,
        cwd=raw.get("cwd"),
        env=raw.get("env"),
        inputs=raw.get("inputs"),
        outputs=raw.get("outputs"),
        clean_env=raw.get("clean-env", raw.get("clean_env")),
    )


def normalize_task(name: str, raw: str | list[Any] | dict[str, Any]) -> Task:
    """Convert a single raw task value into a Task object.

    Handles all the shorthand forms:
    - ``"command string"``  (simple string command)
    - ``["dep1", "dep2"]`` or ``[{"task": ...}]`` (alias / dependency-only)
    - ``{cmd: ..., depends-on: ..., ...}`` (full dict definition)
    """
    if isinstance(raw, str):
        return Task(name=name, cmd=raw)

    if isinstance(raw, list):
        return Task(name=name, depends_on=normalize_depends_on(raw))

    cmd = raw.get("cmd")
    depends_raw = raw.get("depends-on", raw.get("depends_on"))
    env = raw.get("env", {})
    clean_env = raw.get("clean-env", raw.get("clean_env", False))
    default_env = raw.get("default-environment", raw.get("default_environment"))

    platforms: dict[str, TaskOverride] | None = None
    target_raw = raw.get("target")
    if target_raw and isinstance(target_raw, dict):
        platforms = {plat: normalize_override(ov) for plat, ov in target_raw.items()}

    return Task(
        name=name,
        cmd=cmd,
        args=normalize_args(raw.get("args")),
        depends_on=normalize_depends_on(depends_raw),
        cwd=raw.get("cwd"),
        env=env,
        description=raw.get("description"),
        inputs=raw.get("inputs", []),
        outputs=raw.get("outputs", []),
        clean_env=bool(clean_env),
        default_environment=default_env,
        platforms=platforms,
    )


def parse_tasks_and_targets(data: dict[str, Any]) -> dict[str, Task]:
    """Parse ``[tasks]`` and ``[target.<platform>.tasks]`` from a data dict.

    Shared by ``CondaTomlParser``, ``PixiTomlParser``, and
    ``PyprojectTomlParser`` — the core parsing logic is identical
    across all three formats once the root data dict is resolved.
    """

    raw_tasks = data.get("tasks", {})
    if not isinstance(raw_tasks, dict):
        raise TaskParseError("<manifest>", "'tasks' must be a table")

    tasks: dict[str, Task] = {}
    for name, defn in raw_tasks.items():
        tasks[name] = normalize_task(name, defn)

    target = data.get("target", {})
    if isinstance(target, dict):
        _apply_target_overrides(target, tasks)

    return tasks


def parse_feature_tasks(data: dict[str, Any], tasks: dict[str, Task]) -> None:
    """Parse ``[feature.<name>.tasks]`` and their target overrides.

    Merges feature-scoped tasks into *tasks* in place.  Shared by
    ``PixiTomlParser`` and ``PyprojectTomlParser``.
    """
    for feat_name, feat_data in data.get("feature", {}).items():
        if not isinstance(feat_data, dict):
            continue
        feat_tasks = feat_data.get("tasks", {})
        if not isinstance(feat_tasks, dict):
            continue
        for name, defn in feat_tasks.items():
            tasks[name] = normalize_task(name, defn)

        feat_target = feat_data.get("target", {})
        if isinstance(feat_target, dict):
            _apply_target_overrides(feat_target, tasks)


def _apply_target_overrides(
    target: dict[str, Any], tasks: dict[str, Task]
) -> None:
    """Apply ``[target.<platform>.tasks]`` overrides into *tasks*."""
    for platform, platform_data in target.items():
        if not isinstance(platform_data, dict):
            continue
        platform_tasks = platform_data.get("tasks", {})
        for name, defn in platform_tasks.items():
            override = normalize_override(
                defn if isinstance(defn, dict) else {"cmd": defn}
            )
            if name in tasks:
                existing = tasks[name]
                if existing.platforms is None:
                    existing.platforms = {}
                existing.platforms[platform] = override
            else:
                task = normalize_task(name, defn)
                task.platforms = {platform: override}
                tasks[name] = task
