"""Starter boundaries for ROC-AUC and trapezoidal PR-AUC."""

from __future__ import annotations

from collections.abc import Sequence


def roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Return ROC-AUC with tied scores receiving equal, grouped treatment.

    Reject empty input, length mismatch, non-binary labels, non-finite scores, scores
    outside ``[0, 1]``, and labels containing only one class.
    """
    raise NotImplementedError("Implement ROC-AUC without scikit-learn")


def pr_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Return trapezoidal area under a grouped precision-recall curve.

    Start the curve at recall ``0`` and precision ``1``. Add one point after consuming
    every complete group of equal scores in descending threshold order, then integrate
    precision over recall with the trapezoidal rule. Apply the same validation as
    :func:`roc_auc`.
    """
    raise NotImplementedError("Implement trapezoidal PR-AUC without scikit-learn")
