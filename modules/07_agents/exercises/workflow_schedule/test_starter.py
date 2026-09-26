"""Scheduling contracts; no task in this exercise is executed."""

import pytest

from roadmap_tools.exercise import exercise_call

from .starter import Schedule, Task, schedule_workflow


@pytest.mark.student_exercise
def test_dependencies_use_completed_prior_rounds_and_lexicographic_ready_order() -> None:
    tasks = [Task("publish", ("edit",)), Task("read"), Task("edit", ("read",)), Task("audit")]
    assert exercise_call(schedule_workflow, tasks, max_parallel=2) == Schedule(
        (("audit", "read"), ("edit",), ("publish",)),
        (),
    )


@pytest.mark.student_exercise
def test_dependency_completion_waits_for_all_parents() -> None:
    tasks = [Task("join", ("left", "right")), Task("right", ("seed",)), Task("left"), Task("seed")]
    assert exercise_call(schedule_workflow, tasks, max_parallel=2) == Schedule(
        (("left", "seed"), ("right",), ("join",)),
        (),
    )


@pytest.mark.student_exercise
def test_budget_reports_sorted_unfinished_tasks_without_empty_rounds() -> None:
    tasks = [Task("z", ("a",)), Task("c"), Task("b"), Task("a")]
    assert exercise_call(schedule_workflow, tasks, max_parallel=2, max_rounds=1) == Schedule(
        (("a", "b"),),
        ("c", "z"),
    )
    assert exercise_call(schedule_workflow, tasks, max_parallel=2, max_rounds=2) == Schedule(
        (("a", "b"), ("c", "z")),
        (),
    )


@pytest.mark.student_exercise
def test_single_slot_and_input_permutations_are_deterministic_without_mutation() -> None:
    tasks = [Task("c", ("a",)), Task("b"), Task("a")]
    before = tasks.copy()
    expected = Schedule((("a",), ("b",), ("c",)), ())
    assert exercise_call(schedule_workflow, tasks, max_parallel=1) == expected
    assert exercise_call(schedule_workflow, list(reversed(tasks)), max_parallel=1) == expected
    assert tasks == before


@pytest.mark.student_exercise
def test_empty_and_one_task_finish_without_padding() -> None:
    assert exercise_call(schedule_workflow, []) == Schedule((), ())
    assert exercise_call(schedule_workflow, [Task("a")], max_parallel=20) == Schedule((("a",),), ())


@pytest.mark.student_exercise
@pytest.mark.parametrize("max_rounds", [1, 10])
def test_cycle_is_rejected_even_when_budget_would_end_before_reaching_it(max_rounds: int) -> None:
    tasks = [Task("free"), Task("a", ("b",)), Task("b", ("a",))]
    with pytest.raises(ValueError, match="cycle"):
        exercise_call(schedule_workflow, tasks, max_parallel=1, max_rounds=max_rounds)


@pytest.mark.parametrize(
    "tasks",
    [
        [Task("")],
        [Task(" a")],
        [Task("a"), Task("a")],
        [Task("a", ("missing",))],
        [Task("a", ("a",))],
        [Task("a"), Task("b", ("a", "a"))],
    ],
)
def test_invalid_graph_contract(tasks: list[Task]) -> None:
    with pytest.raises(ValueError, match=r"task IDs|dependencies|depend on itself"):
        exercise_call(schedule_workflow, tasks)


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_invalid_limits_for_empty_input(value: object) -> None:
    with pytest.raises(ValueError, match="max_parallel"):
        exercise_call(schedule_workflow, [], max_parallel=value)
    with pytest.raises(ValueError, match="max_rounds"):
        exercise_call(schedule_workflow, [], max_rounds=value)
