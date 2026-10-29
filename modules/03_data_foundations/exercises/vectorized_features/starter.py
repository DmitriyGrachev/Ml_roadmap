"""Learner-owned masked reduction and cosine ranking boundaries."""

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]


def masked_standardize(
    values: FloatArray, observed: npt.NDArray[np.bool_]
) -> tuple[FloatArray, FloatArray, FloatArray, npt.NDArray[np.int64]]:
    """Return (standardized, mean, scale, count), reducing rows with ddof=0."""
    raise NotImplementedError("Implement masked column standardization without input mutation")


def topk_cosine(
    queries: FloatArray, candidates: FloatArray, k: int
) -> tuple[npt.NDArray[np.int64], FloatArray]:
    """Return (indices, scores), ordered by descending cosine then candidate index."""
    raise NotImplementedError("Implement deterministic cosine top-k with zero-vector policy")
