"""DAG resolution and topological sort for task dependencies."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from .exceptions import CyclicDependencyError, TaskNotFoundError

if TYPE_CHECKING:
    from .models import Task


def resolve_execution_order(
    target: str,
    tasks: dict[str, Task],
    *,
    skip_deps: bool = False,
) -> list[str]:
    """Return task names in the order they should execute to run *target*.

    Uses Kahn's algorithm for topological sort. Only the transitive
    closure of *target*'s dependencies is included -- unrelated tasks
    are omitted.

    Raises ``TaskNotFoundError`` if *target* or any dependency is missing.
    Raises ``CyclicDependencyError`` if the dependency graph has a cycle.
    """
    if target not in tasks:
        raise TaskNotFoundError(target, list(tasks.keys()))

    if skip_deps:
        return [target]

    reachable = _collect_reachable(target, tasks)
    return _topological_sort(reachable, tasks)


def _collect_reachable(target: str, tasks: dict[str, Task]) -> set[str]:
    """BFS to gather all tasks reachable via depends-on from *target*."""
    visited: set[str] = set()
    queue = deque([target])
    while queue:
        name = queue.popleft()
        if name in visited:
            continue
        if name not in tasks:
            raise TaskNotFoundError(name, list(tasks.keys()))
        visited.add(name)
        for dep in tasks[name].depends_on:
            if dep.task not in visited:
                queue.append(dep.task)
    return visited


def _topological_sort(names: set[str], tasks: dict[str, Task]) -> list[str]:
    """Kahn's algorithm over the subset *names*."""
    in_degree: dict[str, int] = {n: 0 for n in names}
    adjacency: dict[str, list[str]] = {n: [] for n in names}

    for name in names:
        for dep in tasks[name].depends_on:
            if dep.task in names:
                adjacency[dep.task].append(name)
                in_degree[name] += 1

    queue: deque[str] = deque(sorted(n for n in names if in_degree[n] == 0))
    order: list[str] = []

    while queue:
        node = queue.popleft()
        order.append(node)
        for successor in sorted(adjacency[node]):
            in_degree[successor] -= 1
            if in_degree[successor] == 0:
                queue.append(successor)

    if len(order) != len(names):
        remaining = names - set(order)
        cycle = _find_cycle(remaining, tasks)
        raise CyclicDependencyError(cycle)

    return order


def _find_cycle(names: set[str], tasks: dict[str, Task]) -> list[str]:
    """Find and return one cycle in the dependency graph as a path."""
    visited: set[str] = set()
    path: list[str] = []
    on_stack: set[str] = set()

    def dfs(node: str) -> list[str] | None:
        visited.add(node)
        on_stack.add(node)
        path.append(node)
        for dep in tasks[node].depends_on:
            if dep.task not in names:
                continue
            if dep.task in on_stack:
                idx = path.index(dep.task)
                return path[idx:] + [dep.task]
            if dep.task not in visited:
                result = dfs(dep.task)
                if result is not None:
                    return result
        path.pop()
        on_stack.discard(node)
        return None

    for name in sorted(names):
        if name not in visited:
            result = dfs(name)
            if result is not None:
                return result
    return list(names)
