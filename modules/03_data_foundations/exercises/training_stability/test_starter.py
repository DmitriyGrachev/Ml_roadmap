"""Catch holdout access, missing refits, split drift across sizes, and unpaired deltas."""

from typing import Any

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from roadmap_tools.exercise import exercise_call

from .starter import classification_sweep, paired_accuracy_interval

pytestmark = pytest.mark.student_exercise


def data() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(31)
    x = rng.normal(size=(80, 3))
    y = (x[:, 0] + 0.8 * x[:, 1] + rng.normal(size=80) > 0.1).astype(np.int64)
    return x, y


def sweep(x: Any, y: Any) -> list[dict[str, Any]]:
    return exercise_call(
        classification_sweep,
        x,
        y,
        holdout_ids=np.arange(65, 80),
        seeds=(2, 11),
        sizes=(18, 35),
        validation_size=15,
    )


def test_all_size_seed_pairs_refit_train_only_and_match_pipeline() -> None:
    x, y = data()
    records = sweep(x, y)
    assert len(records) == 4
    assert {(r["seed"], r["size"]) for r in records} == {(2, 18), (2, 35), (11, 18), (11, 35)}
    for row in records:
        train = np.asarray(row["train_ids"])
        valid = np.asarray(row["validation_ids"])
        order = np.random.default_rng(row["seed"]).permutation(np.arange(65))
        np.testing.assert_array_equal(valid, order[:15])
        np.testing.assert_array_equal(train, order[15 : 15 + row["size"]])
        expected = make_pipeline(
            StandardScaler(), LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000)
        )
        expected.fit(x[train], y[train])
        assert row["accuracy"] == pytest.approx(expected.score(x[valid], y[valid]))


def test_changing_holdout_values_and_labels_cannot_change_development_scores() -> None:
    x, y = data()
    first = sweep(x, y)
    x[65:] = 1e12
    y[65:] = 1 - y[65:]
    second = sweep(x, y)
    assert [r["accuracy"] for r in first] == [r["accuracy"] for r in second]


def test_paired_accuracy_sign_and_nontrivial_percentiles_are_hand_computable() -> None:
    y = np.array([0, 0, 1, 1])
    a = np.array([0, 1, 0, 1])
    b = np.array([0, 0, 1, 0])
    indices = np.array([[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]])
    delta, interval = exercise_call(paired_accuracy_interval, y, a, b, indices)
    assert delta == pytest.approx(0.25)
    np.testing.assert_allclose(interval, [-0.925, 1.0])


def test_identical_predictions_have_exact_zero_paired_uncertainty() -> None:
    delta, interval = exercise_call(
        paired_accuracy_interval,
        np.array([0, 1]),
        np.array([0, 0]),
        np.array([0, 0]),
        np.array([[0, 0], [0, 1], [1, 1]]),
    )
    assert delta == 0
    np.testing.assert_array_equal(interval, [0.0, 0.0])


def test_out_of_range_bootstrap_indices_rejected() -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(
            paired_accuracy_interval,
            np.array([0, 1]),
            np.array([0, 1]),
            np.array([0, 1]),
            np.array([[0, 2]]),
        )


def test_impossible_size_and_one_class_training_rejected() -> None:
    x, y = data()
    with pytest.raises(ValueError, match=r"."):
        exercise_call(
            classification_sweep,
            x,
            y,
            holdout_ids=np.arange(65, 80),
            seeds=(2,),
            sizes=(60,),
            validation_size=15,
        )
    with pytest.raises(ValueError, match=r"."):
        sweep(x, np.zeros(80, dtype=np.int64))
