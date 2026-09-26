"""Checks for fitted-state isolation and robust mixed-column prediction."""

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError
from sklearn.utils.validation import check_is_fitted

from roadmap_tools import exercise_call

from .starter import build_visit_pipeline


def training_rows() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "temperature": [10.0, 20.0, np.nan, 30.0],
            "unused_sensor": [np.nan] * 4,
            "park": ["wood", "lake", np.nan, "wood"],
            "target_leak": [40, 80, 60, 120],
        },
    ).astype({"park": object})


def test_factory_returns_unfitted_independent_pipelines() -> None:
    numeric = ["temperature", "unused_sensor"]
    categorical = ["park"]
    first = exercise_call(build_visit_pipeline, numeric, categorical)
    second = exercise_call(build_visit_pipeline, numeric, categorical)
    assert first is not second
    assert first.named_steps["preprocess"] is not second.named_steps["preprocess"]
    assert first.named_steps["model"] is not second.named_steps["model"]
    with pytest.raises(NotFittedError):
        check_is_fitted(first)
    first.fit(training_rows(), [40, 80, 60, 120])
    with pytest.raises(NotFittedError):
        check_is_fitted(second)
    assert numeric == ["temperature", "unused_sensor"]
    assert categorical == ["park"]


def test_training_statistics_and_output_are_auditable() -> None:
    pipeline = exercise_call(build_visit_pipeline, ["temperature", "unused_sensor"], ["park"])
    pipeline.fit(training_rows(), [40, 80, 60, 120])
    preprocessing = pipeline.named_steps["preprocess"]
    numeric = preprocessing.named_transformers_["num"]
    categorical = preprocessing.named_transformers_["cat"]
    np.testing.assert_allclose(numeric.named_steps["imputer"].statistics_, [20.0, 0.0])
    np.testing.assert_allclose(numeric.named_steps["scaler"].mean_, [20.0, 0.0])
    assert set(categorical.named_steps["encoder"].categories_[0]) == {"wood", "lake", "__missing__"}
    assert preprocessing.remainder == "drop"
    assert pipeline.named_steps["model"].alpha == 1.0
    assert pipeline.named_steps["model"].solver == "svd"
    assert preprocessing.transform(training_rows()).shape == (4, 5)


def test_unknown_categories_missing_values_and_extra_columns_are_safe() -> None:
    pipeline = exercise_call(build_visit_pipeline, ["temperature", "unused_sensor"], ["park"])
    pipeline.fit(training_rows(), [40, 80, 60, 120])
    new_rows = pd.DataFrame(
        {
            "temperature": [1000.0, np.nan],
            "unused_sensor": [np.nan, 9.0],
            "park": ["meadow", np.nan],
            "target_leak": [99999, -99999],
        },
    )
    new_rows = new_rows.astype({"park": object})
    original = new_rows.copy(deep=True)
    predictions = pipeline.predict(new_rows)
    assert predictions.shape == (2,)
    assert np.isfinite(predictions).all()
    np.testing.assert_allclose(predictions, pipeline.predict(new_rows.drop(columns="target_leak")))
    preprocessor = pipeline.named_steps["preprocess"]
    np.testing.assert_allclose(
        preprocessor.named_transformers_["num"].named_steps["scaler"].mean_, [20, 0]
    )
    encoded = preprocessor.named_transformers_["cat"].transform(new_rows[["park"]])
    np.testing.assert_array_equal(encoded[0], [0.0, 0.0, 0.0])
    pd.testing.assert_frame_equal(new_rows, original)


def test_all_missing_object_category_is_retained_and_predicts_new_categories() -> None:
    frame = pd.DataFrame(
        {
            "temperature": [10.0, 20.0, 30.0],
            "park": pd.Series([np.nan, np.nan, np.nan], dtype=object),
        }
    )
    original = frame.copy(deep=True)
    pipeline = exercise_call(build_visit_pipeline, ["temperature"], ["park"])
    pipeline.fit(frame, [40.0, 80.0, 120.0])
    preprocessor = pipeline.named_steps["preprocess"]
    categorical = preprocessor.named_transformers_["cat"]
    assert categorical.named_steps["imputer"].keep_empty_features is True
    assert categorical.named_steps["encoder"].categories_[0].tolist() == ["__missing__"]
    assert preprocessor.transform(frame).shape == (3, 2)

    new_rows = pd.DataFrame(
        {
            "temperature": [15.0, 25.0],
            "park": pd.Series([np.nan, "meadow"], dtype=object),
        }
    )
    np.testing.assert_array_equal(categorical.transform(new_rows[["park"]]), [[1.0], [0.0]])
    predictions = pipeline.predict(new_rows)
    assert predictions.shape == (2,)
    assert np.isfinite(predictions).all()
    pd.testing.assert_frame_equal(frame, original)


def test_fitting_preserves_input_and_feature_declarations() -> None:
    frame = training_rows()
    original = frame.copy(deep=True)
    numeric = ["temperature", "unused_sensor"]
    categorical = ["park"]
    pipeline = exercise_call(build_visit_pipeline, numeric, categorical)
    pipeline.fit(frame, [40, 80, 60, 120])
    pd.testing.assert_frame_equal(frame, original)
    assert numeric == ["temperature", "unused_sensor"]
    assert categorical == ["park"]


@pytest.mark.parametrize(
    ("numeric", "categorical"),
    [
        ([], ["park"]),
        (["temperature"], []),
        (["temperature", "temperature"], ["park"]),
        (["temperature"], ["park", "park"]),
        (["park"], ["park"]),
        ([""], ["park"]),
        (["temperature"], ["   "]),
    ],
)
def test_invalid_feature_declarations_are_rejected(
    numeric: list[str], categorical: list[str]
) -> None:
    with pytest.raises(ValueError, match=r"feature|column"):
        exercise_call(build_visit_pipeline, numeric, categorical)
