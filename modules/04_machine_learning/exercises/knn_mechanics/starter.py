"""Student boundary for a small, unweighted Euclidean kNN classifier."""

import numpy as np
from numpy.typing import NDArray


class KNNClassifier:
    """Classify queries from the k closest stored training rows."""

    def __init__(self, k: int) -> None:
        self.k = k

    def fit(self, x: NDArray[np.float64], y: NDArray[np.int64]) -> "KNNClassifier":
        """Validate and copy the training matrix and labels."""
        # TODO: validate finite 2-D x, nonnegative labels and 1 <= k <= n; copy inputs.
        raise NotImplementedError("fit kNN training data")

    def predict(self, x: NDArray[np.float64]) -> NDArray[np.int64]:
        """Return one label per query using deterministic neighbor and vote ties."""
        # TODO: validate queries; calculate Euclidean distances without implicit scaling.
        # TODO: break distance ties by training row, then vote ties by smallest label.
        raise NotImplementedError("predict kNN labels")
