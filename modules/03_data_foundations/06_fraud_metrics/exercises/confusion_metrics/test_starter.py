"""Acceptance tests for the confusion-metric student boundaries."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from roadmap_tools import exercise_call

from .starter import ConfusionCounts, accuracy, confusion_counts, f1, precision, recall


def test_confusion_counts_has_the_documented_immutable_schema() -> None:
    assert [field.name for field in fields(ConfusionCounts)] == ["tp", "fp", "tn", "fn"]
    counts = ConfusionCounts(tp=1, fp=2, tn=3, fn=4)
    field_name = "tp"

    with pytest.raises(FrozenInstanceError):
        setattr(counts, field_name, 0)


def test_counts_each_binary_classification_outcome() -> None:
    counts = exercise_call(
        confusion_counts,
        labels=[1, 0, 0, 1],
        predictions=[1, 1, 0, 0],
    )

    assert counts == ConfusionCounts(tp=1, fp=1, tn=1, fn=1)


def test_rejects_label_prediction_length_mismatch() -> None:
    with pytest.raises(ValueError, match="length"):
        exercise_call(confusion_counts, labels=[1, 0], predictions=[1])


@pytest.mark.parametrize(
    ("labels", "predictions"),
    [([1, 2], [1, 0]), ([1, 0], [1, -1])],
)
def test_rejects_non_binary_labels_or_predictions(
    labels: list[int], predictions: list[int]
) -> None:
    with pytest.raises(ValueError, match=r"binary|0|1"):
        exercise_call(confusion_counts, labels=labels, predictions=predictions)


def test_accuracy_is_one_for_a_perfect_predictor() -> None:
    result = exercise_call(accuracy, ConfusionCounts(tp=2, fp=0, tn=3, fn=0))

    assert result == pytest.approx(1.0)


def test_precision_is_one_for_a_perfect_predictor() -> None:
    result = exercise_call(precision, ConfusionCounts(tp=2, fp=0, tn=3, fn=0))

    assert result == pytest.approx(1.0)


def test_recall_is_one_for_a_perfect_predictor() -> None:
    result = exercise_call(recall, ConfusionCounts(tp=2, fp=0, tn=3, fn=0))

    assert result == pytest.approx(1.0)


def test_f1_is_one_for_a_perfect_predictor() -> None:
    result = exercise_call(f1, ConfusionCounts(tp=2, fp=0, tn=3, fn=0))

    assert result == pytest.approx(1.0)


def test_accuracy_is_one_half_for_mixed_counts() -> None:
    result = exercise_call(accuracy, ConfusionCounts(tp=1, fp=1, tn=1, fn=1))

    assert result == pytest.approx(0.5)


def test_precision_is_one_half_for_mixed_counts() -> None:
    result = exercise_call(precision, ConfusionCounts(tp=1, fp=1, tn=1, fn=1))

    assert result == pytest.approx(0.5)


def test_recall_is_one_half_for_mixed_counts() -> None:
    result = exercise_call(recall, ConfusionCounts(tp=1, fp=1, tn=1, fn=1))

    assert result == pytest.approx(0.5)


def test_f1_is_one_half_for_mixed_counts() -> None:
    result = exercise_call(f1, ConfusionCounts(tp=1, fp=1, tn=1, fn=1))

    assert result == pytest.approx(0.5)


def test_all_negative_predictor_is_99_9_percent_accurate() -> None:
    result = exercise_call(accuracy, ConfusionCounts(tp=0, fp=0, tn=999, fn=1))

    assert result == pytest.approx(0.999)


def test_all_negative_predictor_has_zero_fraud_recall() -> None:
    result = exercise_call(recall, ConfusionCounts(tp=0, fp=0, tn=999, fn=1))

    assert result == pytest.approx(0.0)


def test_accuracy_defaults_to_zero_for_an_empty_count_set() -> None:
    counts = ConfusionCounts(tp=0, fp=0, tn=0, fn=0)

    assert exercise_call(accuracy, counts) == pytest.approx(0.0)


def test_accuracy_uses_custom_zero_division_for_an_empty_count_set() -> None:
    counts = ConfusionCounts(tp=0, fp=0, tn=0, fn=0)

    assert exercise_call(accuracy, counts, zero_division=0.25) == pytest.approx(0.25)


def test_precision_defaults_to_zero_for_no_positive_predictions() -> None:
    counts = ConfusionCounts(tp=0, fp=0, tn=4, fn=1)

    assert exercise_call(precision, counts) == pytest.approx(0.0)


def test_precision_uses_custom_zero_division_for_no_positive_predictions() -> None:
    counts = ConfusionCounts(tp=0, fp=0, tn=4, fn=1)

    assert exercise_call(precision, counts, zero_division=0.25) == pytest.approx(0.25)


def test_recall_defaults_to_zero_for_no_actual_positives() -> None:
    counts = ConfusionCounts(tp=0, fp=1, tn=4, fn=0)

    assert exercise_call(recall, counts) == pytest.approx(0.0)


def test_recall_uses_custom_zero_division_for_no_actual_positives() -> None:
    counts = ConfusionCounts(tp=0, fp=1, tn=4, fn=0)

    assert exercise_call(recall, counts, zero_division=0.25) == pytest.approx(0.25)


def test_f1_defaults_to_zero_when_no_positive_class_is_present() -> None:
    counts = ConfusionCounts(tp=0, fp=0, tn=4, fn=0)

    assert exercise_call(f1, counts) == pytest.approx(0.0)


def test_f1_uses_custom_zero_division_when_no_positive_class_is_present() -> None:
    counts = ConfusionCounts(tp=0, fp=0, tn=4, fn=0)

    assert exercise_call(f1, counts, zero_division=0.25) == pytest.approx(0.25)


def test_f1_is_defined_as_zero_when_false_positives_and_false_negatives_exist() -> None:
    counts = ConfusionCounts(tp=0, fp=1, tn=4, fn=1)

    assert exercise_call(f1, counts, zero_division=0.25) == pytest.approx(0.0)
