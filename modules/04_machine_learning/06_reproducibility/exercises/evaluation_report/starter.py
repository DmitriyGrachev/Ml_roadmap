"""Produce JSON-compatible metrics with explicit threshold and provenance."""

from collections.abc import Sequence
from typing import TypedDict


class BinaryMetrics(TypedDict):
    count: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    brier: float


class EvaluationReport(TypedDict):
    schema_version: int
    model_name: str
    seed: int
    dataset_sha256: str
    threshold: float
    metrics: BinaryMetrics
    slices: dict[str, BinaryMetrics]
    versions: dict[str, str]


def build_evaluation_report(
    y_true: Sequence[int],
    probabilities: Sequence[float],
    slices: Sequence[str],
    *,
    threshold: float,
    seed: int,
    dataset_sha256: str,
    model_name: str,
) -> EvaluationReport:
    """Return overall/slice binary metrics and provenance without writing files.

    Use inclusive thresholding and the README's explicit undefined-metric rules.
    The checksum is caller-supplied provenance, never a signal to trust model loading.
    """
    raise NotImplementedError("Implement the reproducible evaluation report")
