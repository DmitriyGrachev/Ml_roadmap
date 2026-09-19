from collections.abc import Callable

import pytest

from roadmap_tools.exercise import exercise_call


def test_exercise_call_returns_completed_value() -> None:
    assert exercise_call(lambda value: value * 2, 21) == 42


@pytest.mark.student_exercise
def test_unimplemented_operation_is_expected_incomplete() -> None:
    def unfinished() -> None:
        raise NotImplementedError("student boundary")

    exercise_call(unfinished)


def test_exercise_call_does_not_hide_other_errors() -> None:
    operation: Callable[[], None] = lambda: (_ for _ in ()).throw(ValueError("bad input"))
    with pytest.raises(ValueError, match="bad input"):
        exercise_call(operation)
