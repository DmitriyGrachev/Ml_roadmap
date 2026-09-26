"""Hand-counted multiclass wildlife observations."""

# Error message wording is intentionally outside this exercise's contract.
# ruff: noqa: PT011
import pytest

from roadmap_tools.exercise import exercise_call

from .starter import multiclass_report

pytestmark = pytest.mark.student_exercise


def test_confusion_orientation_and_per_class_metrics() -> None:
    result = exercise_call(
        multiclass_report,
        ("owl", "owl", "fox", "fox", "deer"),
        ("owl", "fox", "fox", "deer", "deer"),
        labels=("owl", "fox", "deer"),
    )
    assert result.confusion == ((1, 1, 0), (0, 1, 1), (0, 0, 1))
    assert [item.label for item in result.classes] == ["owl", "fox", "deer"]
    assert [item.support for item in result.classes] == [2, 2, 1]
    assert [item.precision for item in result.classes] == pytest.approx([1.0, 0.5, 0.5])
    assert [item.recall for item in result.classes] == pytest.approx([0.5, 0.5, 1.0])
    assert [item.f1 for item in result.classes] == pytest.approx([2 / 3, 0.5, 2 / 3])
    assert result.accuracy == pytest.approx(0.6)
    assert result.macro_f1 == pytest.approx(11 / 18)


def test_labels_control_order_including_absent_classes() -> None:
    result = exercise_call(multiclass_report, ("owl",), ("owl",), labels=("fox", "owl"))
    assert result.confusion == ((0, 0), (0, 1))
    assert result.classes[0].support == 0
    assert (result.classes[0].precision, result.classes[0].recall, result.classes[0].f1) == (
        0.0,
        0.0,
        0.0,
    )
    assert result.macro_f1 == 0.5
    assert result.accuracy == 1.0


def test_empty_observations_keep_the_complete_label_space() -> None:
    result = exercise_call(multiclass_report, (), (), labels=("owl", "fox"))
    assert result.confusion == ((0, 0), (0, 0))
    assert [item.support for item in result.classes] == [0, 0]
    assert [item.f1 for item in result.classes] == [0.0, 0.0]
    assert result.accuracy == result.macro_f1 == 0.0


def test_no_correct_predictions_and_zero_prediction_denominator() -> None:
    result = exercise_call(multiclass_report, ("owl", "owl"), ("fox", "fox"), labels=("owl", "fox"))
    assert result.confusion == ((0, 2), (0, 0))
    assert [item.precision for item in result.classes] == [0.0, 0.0]
    assert [item.recall for item in result.classes] == [0.0, 0.0]
    assert result.accuracy == result.macro_f1 == 0.0


def test_inputs_are_not_mutated() -> None:
    actual, predicted, labels = ("fox", "owl"), ("owl", "owl"), ("owl", "fox")
    first = exercise_call(multiclass_report, actual, predicted, labels=labels)
    assert (actual, predicted, labels) == (("fox", "owl"), ("owl", "owl"), ("owl", "fox"))
    assert first == exercise_call(multiclass_report, actual, predicted, labels=labels)


@pytest.mark.parametrize("labels", [(), ("owl", "owl"), (" ", "owl")])
def test_invalid_explicit_labels(labels: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        exercise_call(multiclass_report, (), (), labels=labels)


@pytest.mark.parametrize(
    ("actual", "predicted"),
    [(("owl",), ()), (("new",), ("owl",)), (("owl",), ("new",))],
)
def test_mismatched_or_unknown_observations(
    actual: tuple[str, ...], predicted: tuple[str, ...]
) -> None:
    with pytest.raises(ValueError):
        exercise_call(multiclass_report, actual, predicted, labels=("owl", "fox"))
