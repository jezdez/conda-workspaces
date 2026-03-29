"""Tests for conda_workspaces.graph."""

from __future__ import annotations

import pytest

from conda_workspaces.exceptions import CyclicDependencyError, TaskNotFoundError
from conda_workspaces.graph import resolve_execution_order
from conda_workspaces.models import Task, TaskDependency


def test_single_task():
    tasks = {"build": Task(name="build", cmd="make")}
    order = resolve_execution_order("build", tasks)
    assert order == ["build"]


def test_linear_chain(task_with_deps):
    order = resolve_execution_order("test", task_with_deps)
    assert order == ["configure", "build", "test"]


def test_diamond_dependency():
    tasks = {
        "a": Task(name="a", cmd="a"),
        "b": Task(
            name="b",
            cmd="b",
            depends_on=[TaskDependency(task="a")],
        ),
        "c": Task(
            name="c",
            cmd="c",
            depends_on=[TaskDependency(task="a")],
        ),
        "d": Task(
            name="d",
            cmd="d",
            depends_on=[
                TaskDependency(task="b"),
                TaskDependency(task="c"),
            ],
        ),
    }
    order = resolve_execution_order("d", tasks)
    assert order[0] == "a"
    assert order[-1] == "d"
    assert set(order) == {"a", "b", "c", "d"}
    assert order.index("a") < order.index("b")
    assert order.index("a") < order.index("c")


def test_skip_unrelated_tasks(task_with_deps):
    tasks = {
        **task_with_deps,
        "unrelated": Task(name="unrelated", cmd="echo hi"),
    }
    order = resolve_execution_order("test", tasks)
    assert "unrelated" not in order


def test_skip_deps(task_with_deps):
    order = resolve_execution_order("test", task_with_deps, skip_deps=True)
    assert order == ["test"]


@pytest.mark.parametrize(
    ("target", "tasks"),
    [
        (
            "missing",
            {"build": Task(name="build", cmd="make")},
        ),
        (
            "build",
            {
                "build": Task(
                    name="build",
                    cmd="make",
                    depends_on=[TaskDependency(task="missing")],
                ),
            },
        ),
    ],
    ids=["target-missing", "dependency-missing"],
)
def test_task_not_found(target, tasks):
    with pytest.raises(TaskNotFoundError):
        resolve_execution_order(target, tasks)


@pytest.mark.parametrize(
    "tasks",
    [
        pytest.param(
            {
                "a": Task(
                    name="a",
                    cmd="a",
                    depends_on=[TaskDependency(task="a")],
                ),
            },
            id="self-cycle",
        ),
        pytest.param(
            {
                "a": Task(
                    name="a",
                    cmd="a",
                    depends_on=[TaskDependency(task="b")],
                ),
                "b": Task(
                    name="b",
                    cmd="b",
                    depends_on=[TaskDependency(task="a")],
                ),
            },
            id="two-node-cycle",
        ),
        pytest.param(
            {
                "a": Task(
                    name="a",
                    cmd="a",
                    depends_on=[TaskDependency(task="c")],
                ),
                "b": Task(
                    name="b",
                    cmd="b",
                    depends_on=[TaskDependency(task="a")],
                ),
                "c": Task(
                    name="c",
                    cmd="c",
                    depends_on=[TaskDependency(task="b")],
                ),
            },
            id="three-node-cycle",
        ),
    ],
)
def test_cycle_detection(tasks):
    with pytest.raises(CyclicDependencyError):
        resolve_execution_order("a", tasks)


def test_alias_in_order():
    tasks = {
        "test": Task(name="test", cmd="pytest"),
        "lint": Task(name="lint", cmd="ruff check ."),
        "check": Task(
            name="check",
            depends_on=[
                TaskDependency(task="test"),
                TaskDependency(task="lint"),
            ],
        ),
    }
    order = resolve_execution_order("check", tasks)
    assert order[-1] == "check"
    assert set(order) == {"test", "lint", "check"}
