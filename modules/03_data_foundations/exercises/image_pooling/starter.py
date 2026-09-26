"""Student boundary for vectorized downsampling of grayscale images."""

import numpy as np
import numpy.typing as npt


def block_means(
    image: npt.NDArray[np.float64], block_shape: tuple[int, int]
) -> npt.NDArray[np.float64]:
    """Average nonoverlapping spatial blocks into a fresh float64 image."""
    # TODO: validate, reshape into row/block/column/block axes, then reduce block axes.
    raise NotImplementedError("pool grayscale image blocks")
