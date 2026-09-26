"""Student boundary for planning an offline, bounded dependency workflow."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """A named task and IDs that must finish before it becomes ready."""

    id: str
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class Schedule:
    """Planned rounds and IDs left unfinished when the round budget runs out."""

    rounds: tuple[tuple[str, ...], ...]
    unfinished: tuple[str, ...]


def schedule_workflow(
    tasks: Sequence[Task],
    *,
    max_parallel: int = 2,
    max_rounds: int = 10,
) -> Schedule:
    """Validate a DAG and plan deterministic ready-task batches within a budget."""
    if type(max_parallel) is not int or max_parallel < 1:
        raise ValueError("max_parallel must be a positive integer")
    if type(max_rounds) is not int or max_rounds < 1:
        raise ValueError("max_rounds must be a positive integer")
    ids: set[str] = set()
    for task in tasks:
        if not isinstance(task.id, str) or not task.id or task.id != task.id.strip():
            raise ValueError("task IDs must be nonblank strings without outer whitespace")
        if task.id in ids:
            raise ValueError("task IDs must be unique")
        ids.add(task.id)
    for task in tasks:
        if any(
            not isinstance(dependency, str) or dependency not in ids
            for dependency in task.dependencies
        ):
            raise ValueError("dependencies must refer to known task IDs")
        if len(task.dependencies) != len(set(task.dependencies)):
            raise ValueError("dependencies must be unique for each task")
        if task.id in task.dependencies:
            raise ValueError("a task cannot depend on itself")
    # TODO: reject cycles, then schedule deterministic rounds up to the round budget.
    raise NotImplementedError("schedule bounded workflow")
