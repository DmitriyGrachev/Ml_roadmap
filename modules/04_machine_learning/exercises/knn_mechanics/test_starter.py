"""Behavioral contract for a small brute-force kNN classifier."""

import numpy as np
import pytest
from sklearn.neighbors import KNeighborsClassifier

from roadmap_tools.exercise import exercise_call

from .starter import KNNClassifier

pytestmark = pytest.mark.student_exercise


def _comparison_data() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    train = np.array([[0.0, 0.0], [1.0, 4.1], [4.0, 0.0], [5.0, 5.0]])
    labels = np.array([0, 1, 1, 2], dtype=np.int64)
    queries = np.array([[0.1, 0.2], [3.9, 0.2], [4.8, 4.7]])
    return train, labels, queries


def test_comparison_fixture_has_no_equal_distances() -> None:
    train, _, queries = _comparison_data()
    for query in queries:
        distances = np.linalg.norm(train - query, axis=1)
        assert np.unique(distances).size == train.shape[0]


def test_predictions_match_brute_force_sklearn_without_ties() -> None:
    train, labels, queries = _comparison_data()
    expected = KNeighborsClassifier(n_neighbors=3, algorithm="brute", weights="uniform")
    expected.fit(train, labels)

    model = KNNClassifier(k=3)
    assert exercise_call(model.fit, train, labels) is model
    actual = exercise_call(model.predict, queries)
    np.testing.assert_array_equal(actual, expected.predict(queries))
    assert actual.dtype == np.int64
    assert actual.shape == (len(queries),)


def test_equal_distances_prefer_earlier_training_row() -> None:
    model = KNNClassifier(k=1)
    exercise_call(model.fit, np.array([[0.0], [2.0]]), np.array([5, 1], dtype=np.int64))
    np.testing.assert_array_equal(exercise_call(model.predict, np.array([[1.0]])), [5])


def test_equal_vote_counts_prefer_smallest_label() -> None:
    model = KNNClassifier(k=2)
    exercise_call(model.fit, np.array([[0.0], [3.0]]), np.array([9, 3], dtype=np.int64))
    np.testing.assert_array_equal(exercise_call(model.predict, np.array([[0.2]])), [3])


@pytest.mark.parametrize(("k", "expected"), [(1, 8), (3, 4)])
def test_k_one_and_all_training_rows(k: int, expected: int) -> None:
    model = KNNClassifier(k=k)
    exercise_call(
        model.fit,
        np.array([[0.0], [3.0], [8.0]]),
        np.array([8, 4, 4], dtype=np.int64),
    )
    np.testing.assert_array_equal(exercise_call(model.predict, np.array([[0.1]])), [expected])


def test_fit_copies_training_inputs() -> None:
    train = np.array([[0.0], [10.0]])
    labels = np.array([3, 7], dtype=np.int64)
    model = KNNClassifier(k=1)
    exercise_call(model.fit, train, labels)
    train[0, 0] = 100.0
    labels[0] = 99
    np.testing.assert_array_equal(exercise_call(model.predict, np.array([[0.1]])), [3])


def test_predict_does_not_change_queries() -> None:
    model = KNNClassifier(k=1)
    exercise_call(model.fit, np.array([[0.0]]), np.array([3], dtype=np.int64))
    queries = np.array([[0.1], [0.2]])
    exercise_call(model.predict, queries)
    np.testing.assert_array_equal(queries, [[0.1], [0.2]])


def test_predict_before_fit_rejected() -> None:
    with pytest.raises(ValueError, match=r"fit|train"):
        exercise_call(KNNClassifier(k=1).predict, np.array([[1.0]]))


@pytest.mark.parametrize(
    ("train", "labels", "k"),
    [
        (np.empty((0, 1)), np.array([], dtype=np.int64), 1),
        (np.empty((2, 0)), np.array([0, 1], dtype=np.int64), 1),
        (np.array([1.0, 2.0]), np.array([0, 1], dtype=np.int64), 1),
        (np.array([[[1.0]]]), np.array([0], dtype=np.int64), 1),
        (np.array([[1.0], [2.0]]), np.array([0], dtype=np.int64), 1),
        (np.array([[1.0]]), np.array([[0]], dtype=np.int64), 1),
        (np.array([[float("nan")]]), np.array([0], dtype=np.int64), 1),
        (np.array([[float("inf")]]), np.array([0], dtype=np.int64), 1),
        (np.array([[1.0]]), np.array([-1], dtype=np.int64), 1),
        (np.array([[1.0]]), np.array([0], dtype=np.int64), 0),
        (np.array([[1.0]]), np.array([0], dtype=np.int64), 2),
    ],
)
def test_invalid_training_data_rejected(train: np.ndarray, labels: np.ndarray, k: int) -> None:
    with pytest.raises(ValueError, match=r"."):
        exercise_call(KNNClassifier(k=k).fit, train, labels)


@pytest.mark.parametrize(
    "queries",
    [
        np.array([1.0]),
        np.array([[1.0, 2.0]]),
        np.array([[float("nan")]]),
        np.array([[float("inf")]]),
    ],
)
def test_invalid_queries_rejected(queries: np.ndarray) -> None:
    model = KNNClassifier(k=1)
    exercise_call(model.fit, np.array([[1.0]]), np.array([0], dtype=np.int64))
    with pytest.raises(ValueError, match=r"."):
        exercise_call(model.predict, queries)
