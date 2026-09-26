"""Known fold scores distinguish leakage, sign, model and ordering mistakes."""

import numpy as np
import pandas as pd
import pytest

from roadmap_tools import exercise_call

from .starter import compare_regressors


def route_data() -> tuple[pd.DataFrame, pd.Series]:
    return (
        pd.DataFrame(
            {"distance": [0.0, 1.0, np.nan, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 50.0]}
        ),
        pd.Series(np.arange(12, dtype=float) * 2 + 3, name="minutes"),
    )


def test_exact_fold_metrics_detect_leakage_and_negative_score_mistakes() -> None:
    features, target = route_data()
    scores = exercise_call(compare_regressors, features, target)
    assert [score.name for score in scores] == ["tree", "baseline", "ridge"]
    expected = {
        "baseline": (9.185185185185185, 4.444444444444445, 7.703703703703703, 2.9629629629629632),
        "ridge": (8.318286058670674, 3.871411792342025, 22.29243062304286, 3.004477625164187),
        "tree": (2.0, 5.0, 3.0, 4.222222222222222),
    }
    for score in scores:
        assert isinstance(score.fold_mae, tuple)
        assert score.fold_mae == pytest.approx(expected[score.name])
        assert score.mean_mae == pytest.approx(float(np.mean(expected[score.name])))
        assert score.std_mae == pytest.approx(float(np.std(expected[score.name], ddof=0)))
        assert all(isinstance(value, float) and value >= 0 for value in score.fold_mae)


def test_reproducible_results_and_preserved_input() -> None:
    features, target = route_data()
    original_x, original_y = features.copy(deep=True), target.copy(deep=True)
    first = exercise_call(compare_regressors, features, target, 3, 7)
    second = exercise_call(compare_regressors, features, target, 3, 7)
    assert first == second
    assert all(len(score.fold_mae) == 3 for score in first)
    pd.testing.assert_frame_equal(features, original_x)
    pd.testing.assert_series_equal(target, original_y)


def test_rows_are_matched_positionally_not_by_index() -> None:
    features, target = route_data()
    original = exercise_call(compare_regressors, features, target)
    target.index = list(reversed(range(12)))
    reordered_labels = exercise_call(compare_regressors, features, target)
    assert reordered_labels == original


def test_constant_target_ties_are_sorted_by_name() -> None:
    scores = exercise_call(
        compare_regressors, pd.DataFrame({"distance": range(8)}), pd.Series([4.0] * 8)
    )
    assert [score.name for score in scores] == ["baseline", "ridge", "tree"]
    for score in scores:
        assert score.fold_mae == (0.0, 0.0, 0.0, 0.0)
        assert score.mean_mae == 0.0
        assert score.std_mae == 0.0


@pytest.mark.parametrize("folds", [0, 1, 13])
def test_invalid_fold_counts_are_rejected(folds: int) -> None:
    features, target = route_data()
    with pytest.raises(ValueError, match="fold"):
        exercise_call(compare_regressors, features, target, folds)


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf])
def test_nonfinite_targets_are_rejected(invalid: float) -> None:
    features, target = route_data()
    target.iloc[0] = invalid
    with pytest.raises(ValueError, match="target"):
        exercise_call(compare_regressors, features, target)


def test_infinite_and_entirely_missing_features_are_rejected() -> None:
    features, target = route_data()
    for values in [[np.inf] + [1.0] * 11, [np.nan] * 12]:
        features["distance"] = values
        with pytest.raises(ValueError, match="feature"):
            exercise_call(compare_regressors, features, target)


def test_empty_mismatched_and_nonnumeric_inputs_are_rejected() -> None:
    features, target = route_data()
    for bad_x, bad_y in [
        (features.iloc[:0], target.iloc[:0]),
        (features, target.iloc[:-1]),
        (pd.DataFrame(index=range(12)), target),
        (pd.DataFrame({"route": ["park"] * 12}), target),
        (features, pd.Series(["slow"] * 12)),
    ]:
        with pytest.raises(ValueError, match=r"feature|target|empty|length|numeric"):
            exercise_call(compare_regressors, bad_x, bad_y)


def test_invalid_feature_names_and_negative_seed_are_rejected() -> None:
    features, target = route_data()
    with pytest.raises(ValueError, match="seed"):
        exercise_call(compare_regressors, features, target, seed=-1)
    for bad_x in [
        features.rename(columns={"distance": ""}),
        pd.concat([features, features], axis=1),
    ]:
        with pytest.raises(ValueError, match="feature"):
            exercise_call(compare_regressors, bad_x, target)
