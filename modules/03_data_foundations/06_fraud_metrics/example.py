"""Count classification outcomes for a tiny synthetic document-labeling batch."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def confusion_counts() -> dict[str, int]:
    """Return one of each confusion-matrix outcome for document labels."""
    actual_sensitive: NDArray[np.bool_] = np.array([True, False, False, True])
    predicted_sensitive: NDArray[np.bool_] = np.array([True, True, False, False])
    return {
        "true_positive": int(np.sum(actual_sensitive & predicted_sensitive)),
        "false_positive": int(np.sum(~actual_sensitive & predicted_sensitive)),
        "true_negative": int(np.sum(~actual_sensitive & ~predicted_sensitive)),
        "false_negative": int(np.sum(actual_sensitive & ~predicted_sensitive)),
    }


def main() -> None:
    """Print the deterministic confusion-matrix counts."""
    print(confusion_counts())


if __name__ == "__main__":
    main()
