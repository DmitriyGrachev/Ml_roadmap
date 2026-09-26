"""Student boundary for hand-auditable multiclass evaluation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClassMetrics:
    """Metrics for one class in the caller's label order."""

    label: str
    support: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True)
class MulticlassReport:
    """Rows are actual labels; columns are predicted labels."""

    confusion: tuple[tuple[int, ...], ...]
    classes: tuple[ClassMetrics, ...]
    accuracy: float
    macro_f1: float


def multiclass_report(
    actual: tuple[str, ...],
    predicted: tuple[str, ...],
    *,
    labels: tuple[str, ...],
) -> MulticlassReport:
    """Build the explicit-label report with zero-safe denominators."""
    if not labels or any(not isinstance(label, str) or not label.strip() for label in labels):
        raise ValueError("labels must be nonempty and contain nonblank strings")
    if len(set(labels)) != len(labels):
        raise ValueError("labels must be unique")
    if len(actual) != len(predicted):
        raise ValueError("actual and predicted lengths must match")
    if any(label not in labels for label in (*actual, *predicted)):
        raise ValueError("all observations must belong to the explicit labels")
    # TODO: count the matrix and derive per-class and aggregate metrics.
    raise NotImplementedError("explicit-label multiclass report")
