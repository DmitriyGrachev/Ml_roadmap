"""Acceptance tests for deterministic metrics, slices and provenance validation."""

import json
import platform

import numpy as np
import pytest
import sklearn

from roadmap_tools import exercise_call

from .starter import build_evaluation_report


def test_overall_and_slice_metrics_include_support_and_probability_error() -> None:
    report = exercise_call(
        build_evaluation_report,
        [0, 1, 1, 0],
        [0.1, 0.8, 0.4, 0.7],
        ["shade", "shade", "sun", "sun"],
        threshold=0.5,
        seed=42,
        dataset_sha256="A" * 64,
        model_name="watering-v1",
    )
    assert report["schema_version"] == 1
    assert report["model_name"] == "watering-v1"
    assert report["seed"] == 42
    assert report["dataset_sha256"] == "a" * 64
    assert report["threshold"] == 0.5
    assert report["metrics"] == pytest.approx(
        {"count": 4, "accuracy": 0.5, "precision": 0.5, "recall": 0.5, "f1": 0.5, "brier": 0.225}
    )
    assert report["slices"]["shade"] == pytest.approx(
        {"count": 2, "accuracy": 1, "precision": 1, "recall": 1, "f1": 1, "brier": 0.025}
    )
    assert report["slices"]["sun"] == pytest.approx(
        {"count": 2, "accuracy": 0, "precision": 0, "recall": 0, "f1": 0, "brier": 0.425}
    )
    assert report["versions"] == {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
    }


def test_precision_recall_and_f1_are_distinct_on_unequal_errors() -> None:
    report = exercise_call(
        build_evaluation_report,
        [1, 1, 1, 0],
        [0.9, 0.8, 0.1, 0.2],
        ["sun"] * 4,
        threshold=0.5,
        seed=0,
        dataset_sha256="1" * 64,
        model_name="test",
    )
    assert report["metrics"]["precision"] == 1
    assert report["metrics"]["recall"] == pytest.approx(2 / 3)
    assert report["metrics"]["f1"] == pytest.approx(0.8)


def test_inclusive_threshold_sorted_slices_and_undefined_metrics() -> None:
    report = exercise_call(
        build_evaluation_report,
        [1, 0, 0],
        [0.5, 0.1, 0.2],
        ["z", "a", "a"],
        threshold=0.5,
        seed=0,
        dataset_sha256="b" * 64,
        model_name="threshold-test",
    )
    assert list(report["slices"]) == ["a", "z"]
    assert report["metrics"]["accuracy"] == 1.0
    assert report["slices"]["a"]["precision"] == 0.0
    assert report["slices"]["a"]["recall"] == 0.0
    assert report["slices"]["a"]["f1"] == 0.0
    assert report["slices"]["z"]["count"] == 1


@pytest.mark.parametrize("threshold", [0.0, 1.0])
def test_threshold_endpoints_are_valid(threshold: float) -> None:
    report = exercise_call(
        build_evaluation_report,
        [1],
        [1.0],
        ["single"],
        threshold=threshold,
        seed=0,
        dataset_sha256="c" * 64,
        model_name="endpoint",
    )
    assert report["metrics"]["accuracy"] == 1.0


def test_report_is_repeatable_json_and_preserves_inputs() -> None:
    labels, probabilities, slices = [0, 1], [0.3, 0.7], ["wood", "lake"]
    first = exercise_call(
        build_evaluation_report,
        labels,
        probabilities,
        slices,
        threshold=0.4,
        seed=5,
        dataset_sha256="d" * 64,
        model_name="v2",
    )
    second = exercise_call(
        build_evaluation_report,
        labels,
        probabilities,
        slices,
        threshold=0.4,
        seed=5,
        dataset_sha256="d" * 64,
        model_name="v2",
    )
    assert first == second
    assert json.loads(json.dumps(first, sort_keys=True, allow_nan=False)) == first
    assert set(first) == {
        "schema_version",
        "model_name",
        "seed",
        "dataset_sha256",
        "threshold",
        "metrics",
        "slices",
        "versions",
    }
    assert isinstance(first["metrics"]["count"], int)
    assert labels == [0, 1]
    assert probabilities == [0.3, 0.7]
    assert slices == ["wood", "lake"]


@pytest.mark.parametrize(
    ("labels", "probabilities", "slices"),
    [
        ([], [], []),
        ([0], [], ["a"]),
        ([0], [0.5], []),
        ([2], [0.5], ["a"]),
        ([0], [np.nan], ["a"]),
        ([0], [np.inf], ["a"]),
        ([0], [-0.1], ["a"]),
        ([0], [1.1], ["a"]),
        ([0], [0.5], [""]),
        ([0], [0.5], ["   "]),
    ],
)
def test_invalid_observations_are_rejected(
    labels: list[int], probabilities: list[float], slices: list[str]
) -> None:
    with pytest.raises(ValueError, match=r"length|label|probabilit|slice|empty"):
        exercise_call(
            build_evaluation_report,
            labels,
            probabilities,
            slices,
            threshold=0.5,
            seed=0,
            dataset_sha256="a" * 64,
            model_name="v1",
        )


@pytest.mark.parametrize("threshold", [-0.1, 1.1, np.nan, np.inf])
def test_invalid_threshold_is_rejected(threshold: float) -> None:
    with pytest.raises(ValueError, match="threshold"):
        exercise_call(
            build_evaluation_report,
            [0],
            [0.1],
            ["a"],
            threshold=threshold,
            seed=0,
            dataset_sha256="a" * 64,
            model_name="v1",
        )


@pytest.mark.parametrize("checksum", ["", "a" * 63, "a" * 65, "z" * 64])
def test_invalid_checksum_is_rejected(checksum: str) -> None:
    with pytest.raises(ValueError, match=r"sha|checksum|hex"):
        exercise_call(
            build_evaluation_report,
            [0],
            [0.1],
            ["a"],
            threshold=0.5,
            seed=0,
            dataset_sha256=checksum,
            model_name="v1",
        )


@pytest.mark.parametrize(("seed", "model_name"), [(-1, "v1"), (0, ""), (0, "   ")])
def test_invalid_run_metadata_is_rejected(seed: int, model_name: str) -> None:
    with pytest.raises(ValueError, match=r"seed|model"):
        exercise_call(
            build_evaluation_report,
            [0],
            [0.1],
            ["a"],
            threshold=0.5,
            seed=seed,
            dataset_sha256="a" * 64,
            model_name=model_name,
        )
