"""Catch holdout leakage, fake retraining, and unpaired resampling."""

import numpy as np
import pytest

from .demo import paired_bootstrap, retraining_sweep


def test_refits_are_repeatable_and_holdout_is_excluded() -> None:
    x = np.arange(60, dtype=float)[:, None]
    y = np.sin(x[:, 0] / 3) + x[:, 0] / 20
    results = retraining_sweep(x, y, holdout_ids=np.arange(50, 60), seeds=(2, 7), sizes=(12, 30))
    assert len(results) == 4
    for row in results:
        assert len(row["train_ids"]) == row["size"]
        assert set(row["train_ids"]).isdisjoint(row["validation_ids"])
        assert max(row["train_ids"]) < 50
        assert max(row["validation_ids"]) < 50
        assert row["mse"] >= 0
    repeat = retraining_sweep(x, y, holdout_ids=np.arange(50, 60), seeds=(2, 7), sizes=(12, 30))
    assert [r["mse"] for r in results] == [r["mse"] for r in repeat]
    assert len({r["mse"] for r in results}) > 1


def test_paired_bootstrap_preserves_row_pairing_and_sign() -> None:
    result = paired_bootstrap(
        np.array([1.0, 4.0, 9.0]), np.array([0.0, 3.0, 8.0]), seed=8, repeats=200
    )
    np.testing.assert_allclose(result, [1.0, 1.0])
    assert paired_bootstrap(np.array([0.0, 0.0]), np.array([1.0, 1.0]), seed=3, repeats=40)[1] < 0


def test_invalid_holdout_and_oversized_training_rejected() -> None:
    with pytest.raises(ValueError, match="holdout"):
        retraining_sweep(
            np.ones((12, 1)), np.ones(12), holdout_ids=np.array([12]), seeds=(1,), sizes=(2,)
        )
    with pytest.raises(ValueError, match="size"):
        retraining_sweep(
            np.ones((12, 1)), np.ones(12), holdout_ids=np.array([10, 11]), seeds=(1,), sizes=(10,)
        )


def test_holdout_label_and_feature_perturbation_cannot_affect_development_scores() -> None:
    x = np.arange(60, dtype=float)[:, None]
    y = np.sin(x[:, 0] / 3) + x[:, 0] / 20
    before = retraining_sweep(x, y, holdout_ids=np.arange(50, 60), seeds=(2, 7), sizes=(12, 30))
    x[50:] = np.nan
    y[50:] = np.inf
    after = retraining_sweep(x, y, holdout_ids=np.arange(50, 60), seeds=(2, 7), sizes=(12, 30))
    assert [r["mse"] for r in before] == [r["mse"] for r in after]


@pytest.mark.parametrize(
    ("baseline", "candidate", "repeats"),
    [
        (np.array([]), np.array([]), 20),
        (np.array([1.0, 2.0]), np.array([1.0]), 20),
        (np.array([1.0, np.nan]), np.array([1.0, 2.0]), 20),
        (np.array([1.0, 2.0]), np.array([1.0, 2.0]), 1),
    ],
)
def test_invalid_paired_losses_are_rejected(
    baseline: np.ndarray, candidate: np.ndarray, repeats: int
) -> None:
    with pytest.raises(ValueError, match=r"."):
        paired_bootstrap(baseline, candidate, seed=2, repeats=repeats)
