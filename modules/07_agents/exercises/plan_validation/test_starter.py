"""Review a proposal's authority and graph without executing its steps."""

# ruff: noqa: PT011 -- The public contract specifies exception classes, not message text.

import pytest

from roadmap_tools import exercise_call

from .starter import PlanStep, validate_plan


def test_accepts_forward_dependencies_and_preserves_declaration_order() -> None:
    steps = (
        PlanStep("describe", "describe", ("lookup",)),
        PlanStep("lookup", "read"),
    )
    assert exercise_call(validate_plan, steps, frozenset({"read", "describe"}), 2) == (
        "describe",
        "lookup",
    )
    assert steps[0].dependencies == ("lookup",)


def test_allows_independent_steps_and_shared_prerequisite() -> None:
    steps = (PlanStep("a", "read"), PlanStep("b", "read", ("a",)), PlanStep("c", "read", ("a",)))
    assert exercise_call(validate_plan, steps, frozenset({"read"}), 3) == ("a", "b", "c")


def test_ungranted_capability_is_denied() -> None:
    with pytest.raises(PermissionError):
        exercise_call(validate_plan, (PlanStep("a", "reserve"),), frozenset({"read"}), 1)


@pytest.mark.parametrize("steps", [(), (PlanStep("a", "read"), PlanStep("b", "read"))])
def test_rejects_empty_or_oversized_plan(steps: tuple[PlanStep, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(validate_plan, steps, frozenset({"read"}), 1)


@pytest.mark.parametrize("limit", [0, 101, True])
def test_rejects_invalid_step_limit(limit: int) -> None:
    with pytest.raises(ValueError):
        exercise_call(validate_plan, (PlanStep("a", "read"),), frozenset({"read"}), limit)


def test_duplicate_step_ids_are_invalid() -> None:
    with pytest.raises(ValueError):
        exercise_call(validate_plan, (PlanStep("a", "read"),) * 2, frozenset({"read"}), 2)


@pytest.mark.parametrize("dependencies", [("missing",), ("a",), ("b", "b")])
def test_rejects_unknown_self_and_duplicate_dependencies(dependencies: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(
            validate_plan,
            (PlanStep("a", "read", dependencies), PlanStep("b", "read")),
            frozenset({"read"}),
            2,
        )


def test_finds_cycle_in_a_disconnected_component() -> None:
    steps = (
        PlanStep("free", "read"),
        PlanStep("a", "read", ("b",)),
        PlanStep("b", "read", ("c",)),
        PlanStep("c", "read", ("a",)),
    )
    with pytest.raises(ValueError):
        exercise_call(validate_plan, steps, frozenset({"read"}), 4)


@pytest.mark.parametrize(
    "step",
    [
        PlanStep("", "read"),
        PlanStep(" a", "read"),
        PlanStep("a", "read "),
        PlanStep("a", ""),
        PlanStep("x" * 81, "read"),
        PlanStep("a", "x" * 81),
    ],
)
def test_rejects_noncanonical_names(step: PlanStep) -> None:
    with pytest.raises(ValueError):
        exercise_call(validate_plan, (step,), frozenset({"read", "read ", ""}), 1)


def test_structural_error_precedes_permission_denial() -> None:
    with pytest.raises(ValueError):
        exercise_call(validate_plan, (PlanStep("a", "denied", ("absent",)),), frozenset(), 1)
