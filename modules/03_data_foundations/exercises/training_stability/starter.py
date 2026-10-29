"""Classification experiment: full refits versus fixed paired predictions."""

from typing import Any

import numpy as np
from numpy.typing import NDArray


def classification_sweep(
    x: NDArray[np.float64],
    y: NDArray[np.int64],
    *,
    holdout_ids: NDArray[np.int64],
    seeds: tuple[int, ...],
    sizes: tuple[int, ...],
    validation_size: int,
) -> list[dict[str, Any]]:
    """Permute development per seed; reserve first validation_size rows; refit each size."""
    # TODO: StandardScaler + LogisticRegression(C=1, solver='lbfgs', max_iter=1000).
    # TODO: return seed,size,train_ids,validation_ids,accuracy for every full refit.
    # Input contract assumes IID rows; reject one-class training partitions.
    raise NotImplementedError("measure classification stability through complete refits")


def paired_accuracy_interval(
    y: NDArray[np.int64],
    baseline: NDArray[np.int64],
    candidate: NDArray[np.int64],
    resample_indices: NDArray[np.int64],
) -> tuple[float, NDArray[np.float64]]:
    """Return candidate-minus-baseline accuracy and its 95% paired percentile interval."""
    # TODO: align all three vectors; use identical sampled row indices for both models.
    raise NotImplementedError("estimate conditional paired accuracy difference")
