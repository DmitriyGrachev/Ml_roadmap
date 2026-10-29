"""Independent group-CV scores and holdout interpretation without refitting."""

from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from roadmap_tools.exercise import exercise_call

from .starter import permutation_report, select_pipeline

pytestmark = pytest.mark.student_exercise


def training_fixture() -> tuple[pd.DataFrame, npt.NDArray[np.int64], npt.NDArray[np.int64]]:
    groups = np.repeat(np.arange(12, dtype=np.int64), 4)
    signal = np.tile([-3.0, -1.0, 1.0, 3.0], 12)
    labels = (signal > 0).astype(np.int64)
    frame = pd.DataFrame(
        {
            "signal": signal,
            "aux": np.where(np.arange(48) % 7 == 0, np.nan, groups.astype(float)),
            "region": np.asarray(["east", "west", np.nan, "east"] * 12, dtype=object),
        },
        index=np.arange(100, 148),
    )
    return frame, labels, groups


def nonseparable_group_fixture() -> tuple[
    pd.DataFrame, npt.NDArray[np.int64], npt.NDArray[np.int64]
]:
    """36 noisy, imbalanced rows: macro-F1 prefers C=1 rather than the smallest C."""
    rng = np.random.default_rng(211)
    numeric = rng.normal(size=(36, 2))
    labels = (numeric[:, 0] + 0.8 * numeric[:, 1] + rng.normal(0, 1.5, size=36) > 0.8).astype(
        np.int64
    )
    frame = pd.DataFrame(
        {
            "signal": numeric[:, 0],
            "aux": numeric[:, 1],
            "region": ["east", "west"] * 18,
        },
        index=np.arange(300, 336),
    )
    groups = np.repeat(np.arange(6, dtype=np.int64), 6)
    return frame, labels, groups


def holdout_fixture() -> tuple[pd.DataFrame, npt.NDArray[np.int64]]:
    frame = pd.DataFrame(
        {
            "signal": [-4.0, -2.0, 2.0, 4.0, -3.0, 3.0],
            "aux": [np.nan, 10000.0, 10000.0, np.nan, 0.0, 0.0],
            "region": ["north", np.nan, "north", "west", "east", "north"],
        },
        index=np.arange(900, 906),
    )
    return frame, np.array([0, 0, 1, 1, 0, 1], dtype=np.int64)


def test_pipeline_components_training_state_unknown_categories_and_no_mutation() -> None:
    frame, labels, groups = training_fixture()
    original, original_labels, original_groups = frame.copy(deep=True), labels.copy(), groups.copy()
    model, table = exercise_call(select_pipeline, frame, labels, groups, seed=19)
    assert isinstance(model, Pipeline)
    preprocessing = model.named_steps["preprocess"]
    numeric = preprocessing.named_transformers_["num"]
    categorical = preprocessing.named_transformers_["cat"]
    assert isinstance(numeric["imputer"], SimpleImputer)
    assert numeric["imputer"].strategy == "median"
    assert numeric["imputer"].keep_empty_features is True
    assert isinstance(numeric["scaler"], StandardScaler)
    assert isinstance(categorical["imputer"], SimpleImputer)
    assert categorical["imputer"].strategy == "constant"
    assert categorical["imputer"].fill_value == "__missing__"
    assert categorical["imputer"].keep_empty_features is True
    assert isinstance(categorical["encoder"], OneHotEncoder)
    assert categorical["encoder"].handle_unknown == "ignore"
    assert isinstance(model.named_steps["model"], LogisticRegression)
    assert model.named_steps["model"].random_state == 19
    assert model.named_steps["model"].max_iter == 200
    assert table["C"].tolist() == [0.1, 1.0, 10.0]
    assert list(table.columns) == [
        "C",
        "split0_test_score",
        "split1_test_score",
        "split2_test_score",
        "mean_test_score",
        "rank_test_score",
    ]
    np.testing.assert_allclose(numeric["imputer"].statistics_, frame[["signal", "aux"]].median())
    x_holdout, _ = holdout_fixture()
    before_holdout = x_holdout.copy(deep=True)
    predictions = model.predict(x_holdout)
    assert predictions.shape == (6,)
    assert set(predictions) <= {0, 1}
    assert set(categorical["encoder"].categories_[0]) == {"east", "west", "__missing__"}
    pd.testing.assert_frame_equal(frame, original)
    pd.testing.assert_frame_equal(x_holdout, before_holdout)
    np.testing.assert_array_equal(labels, original_labels)
    np.testing.assert_array_equal(groups, original_groups)


def test_cv_table_matches_independent_group_disjoint_macro_f1_and_stable_c_choice() -> None:
    frame, labels, groups = training_fixture()
    model, table = exercise_call(select_pipeline, frame, labels, groups, seed=11)
    assert table.shape == (3, 6)
    expected_means = []
    for row, c in enumerate((0.1, 1.0, 10.0)):
        scores = []
        for fold, (train, validation) in enumerate(
            GroupKFold(n_splits=3).split(frame, labels, groups)
        ):
            assert set(groups[train]).isdisjoint(groups[validation])
            candidate = clone(model).set_params(model__C=c)
            candidate.fit(frame.iloc[train], labels[train])
            score = f1_score(
                labels[validation], candidate.predict(frame.iloc[validation]), average="macro"
            )
            scores.append(score)
            assert table.iloc[row][f"split{fold}_test_score"] == pytest.approx(score)
        expected_means.append(float(np.mean(scores)))
    np.testing.assert_allclose(table["mean_test_score"], expected_means)
    expected_ranks = pd.Series(expected_means).rank(method="min", ascending=False).astype(int)
    np.testing.assert_array_equal(table["rank_test_score"], expected_ranks)
    expected_c = (0.1, 1.0, 10.0)[int(np.argmax(expected_means))]
    assert expected_c == model.named_steps["model"].C
    repeated, repeated_table = exercise_call(select_pipeline, frame, labels, groups, seed=11)
    pd.testing.assert_frame_equal(table, repeated_table)
    np.testing.assert_array_equal(model.predict(frame), repeated.predict(frame))


def test_nonseparable_groups_discriminate_macro_f1_and_nontrivial_refit_choice() -> None:
    frame, labels, groups = nonseparable_group_fixture()
    model, table = exercise_call(select_pipeline, frame, labels, groups, seed=11)
    assert table["C"].tolist() == [0.1, 1.0, 10.0]
    np.testing.assert_array_equal(np.bincount(labels), [26, 10])
    macro_scores = np.empty((3, 3))
    accuracy_scores = np.empty((3, 3))
    for row, c in enumerate((0.1, 1.0, 10.0)):
        for fold, (train, validation) in enumerate(
            GroupKFold(n_splits=3).split(frame, labels, groups)
        ):
            assert set(groups[train]).isdisjoint(groups[validation])
            np.testing.assert_array_equal(np.unique(labels[train]), [0, 1])
            candidate = clone(model).set_params(model__C=c)
            candidate.fit(frame.iloc[train], labels[train])
            predicted = candidate.predict(frame.iloc[validation])
            macro_scores[row, fold] = f1_score(labels[validation], predicted, average="macro")
            accuracy_scores[row, fold] = accuracy_score(labels[validation], predicted)

    # Guard the fixture itself: changing scoring or always choosing C=0.1 must be observable.
    assert not np.allclose(macro_scores, accuracy_scores)
    means = macro_scores.mean(axis=1)
    expected_c = (0.1, 1.0, 10.0)[int(np.argmax(means))]
    assert expected_c == 1.0
    for fold in range(3):
        np.testing.assert_allclose(table[f"split{fold}_test_score"], macro_scores[:, fold])
    np.testing.assert_allclose(table["mean_test_score"], means)
    expected_ranks = pd.Series(means).rank(method="min", ascending=False).astype(int)
    np.testing.assert_array_equal(table["rank_test_score"], expected_ranks)
    assert expected_c == model.named_steps["model"].C

    # A changed C attribute alone cannot substitute for refitting with the winning C.
    reference = clone(model).set_params(model__C=expected_c)
    reference.fit(frame, labels)
    np.testing.assert_allclose(
        model.named_steps["model"].coef_, reference.named_steps["model"].coef_
    )
    np.testing.assert_allclose(
        model.named_steps["model"].intercept_, reference.named_steps["model"].intercept_
    )
    np.testing.assert_allclose(model.predict_proba(frame), reference.predict_proba(frame))


def test_each_preprocessing_fit_sees_only_a_training_fold_or_final_train(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame, labels, groups = training_fixture()
    seen: list[frozenset[int]] = []
    original_fit = SimpleImputer.fit

    def record_fit(self: Any, x: pd.DataFrame, y: Any = None, **kwargs: Any) -> Any:
        seen.append(frozenset(x.index))
        return original_fit(self, x, y, **kwargs)

    monkeypatch.setattr(SimpleImputer, "fit", record_fit)
    exercise_call(select_pipeline, frame, labels, groups, seed=5)
    folds = [
        frozenset(frame.index[train])
        for train, _ in GroupKFold(n_splits=3).split(frame, labels, groups)
    ]
    # Two imputers, three Cs times three folds, then one final train-only refit.
    assert len(seen) == 20
    for fold in folds:
        assert seen.count(fold) == 6
    assert seen.count(frozenset(frame.index)) == 2
    assert all(indices in [*folds, frozenset(frame.index)] for indices in seen)


def test_permuted_labels_do_not_retain_signal_quality() -> None:
    frame, labels, groups = training_fixture()
    labels = np.random.default_rng(913).permutation(labels)
    _, table = exercise_call(select_pipeline, frame, labels, groups, seed=19)
    assert table["mean_test_score"].max() < 0.8


def test_empty_numeric_and_categorical_columns_are_retained() -> None:
    frame, labels, groups = training_fixture()
    frame["aux"] = np.nan
    frame["region"] = pd.Series(np.nan, index=frame.index, dtype=object)
    model, _ = exercise_call(select_pipeline, frame, labels, groups, seed=19)
    numeric = model.named_steps["preprocess"].named_transformers_["num"]
    np.testing.assert_allclose(numeric["imputer"].statistics_, [0.0, 0.0])
    assert model.named_steps["preprocess"].transform(frame).shape[1] == 3
    x_holdout, _ = holdout_fixture()
    assert len(model.predict(x_holdout)) == len(x_holdout)


def test_permutation_matches_heldout_sklearn_five_repeats_without_refit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame, labels, groups = training_fixture()
    model, _ = exercise_call(select_pipeline, frame, labels, groups, seed=9)
    x_holdout, y_holdout = holdout_fixture()
    original, original_labels = x_holdout.copy(deep=True), y_holdout.copy()
    before_coef = model.named_steps["model"].coef_.copy()
    expected = permutation_importance(
        model, x_holdout, y_holdout, scoring="f1_macro", n_repeats=5, random_state=9, n_jobs=1
    )

    def blocked_fit(*args: object, **kwargs: object) -> None:
        raise AssertionError("holdout report must never fit")

    monkeypatch.setattr(Pipeline, "fit", blocked_fit)
    report = exercise_call(permutation_report, model, x_holdout, y_holdout, seed=9)
    assert report.columns.tolist() == ["feature", "importance_mean", "importance_std"]
    assert report["feature"].tolist() == frame.columns.tolist()
    np.testing.assert_allclose(report["importance_mean"], expected.importances_mean)
    np.testing.assert_allclose(report["importance_std"], expected.importances_std)
    repeated = exercise_call(permutation_report, model, x_holdout, y_holdout, seed=9)
    pd.testing.assert_frame_equal(report, repeated)
    pd.testing.assert_frame_equal(x_holdout, original)
    np.testing.assert_array_equal(y_holdout, original_labels)
    np.testing.assert_array_equal(model.named_steps["model"].coef_, before_coef)


def test_permutation_preserves_negative_importance_without_search() -> None:
    frame = pd.DataFrame({"signal": [-3.0, -2.0, -1.0, 1.0, 2.0, 3.0], "constant": [0.0] * 6})
    train_labels = np.array([0, 0, 0, 1, 1, 1], dtype=np.int64)
    model = Pipeline(
        [("scale", StandardScaler()), ("model", LogisticRegression(random_state=9, max_iter=200))]
    ).fit(frame, train_labels)
    # A reversed holdout relationship makes shuffling improve the baseline score.
    x_holdout, y_holdout = frame.copy(deep=True), 1 - train_labels
    expected = permutation_importance(
        model, x_holdout, y_holdout, scoring="f1_macro", n_repeats=5, random_state=9, n_jobs=1
    )
    assert expected.importances_mean[0] < 0
    report = exercise_call(permutation_report, model, x_holdout, y_holdout, seed=9)
    assert report["feature"].tolist() == x_holdout.columns.tolist()
    np.testing.assert_allclose(report["importance_mean"], expected.importances_mean)
    np.testing.assert_allclose(report["importance_std"], expected.importances_std)


@pytest.mark.parametrize(
    "problem",
    [
        "labels",
        "groups",
        "few_groups",
        "one_class",
        "infinite",
        "no_numeric",
        "no_category",
        "duplicate_columns",
        "missing_group",
        "single_class_fold",
    ],
)
def test_invalid_training_contract(problem: str) -> None:
    frame, labels, groups = training_fixture()
    if problem == "labels":
        labels = labels[:-1]
    elif problem == "groups":
        groups = groups[:-1]
    elif problem == "few_groups":
        groups = groups % 2
    elif problem == "one_class":
        labels[:] = 0
    elif problem == "single_class_fold":
        labels[:] = 0
        labels[groups == 11] = 1
    elif problem == "infinite":
        frame.loc[frame.index[0], "signal"] = np.inf
    elif problem == "no_numeric":
        frame = frame[["region"]]
    elif problem == "no_category":
        frame = frame[["signal", "aux"]]
    elif problem == "duplicate_columns":
        frame.columns = ["signal", "signal", "region"]
    else:
        groups = groups.astype(float)
        groups[0] = np.nan
    with pytest.raises(ValueError, match=r"."):
        exercise_call(select_pipeline, frame, labels, groups, seed=1)
