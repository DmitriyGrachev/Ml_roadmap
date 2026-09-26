# Pool grayscale image blocks

Difficulty: Medium · Estimated time: 35–50 minutes

## Prerequisites

Module 03 NumPy lesson: shape, reshape, reduction axes, slicing, and array copies.
Know how a two-dimensional image stores rows and columns of pixel intensities.

## Requirements

Implement `block_means(image, block_shape)` in `starter.py` using NumPy reshape
and reductions over axes, without Python loops over pixels or image blocks.

- Input is a float64 NumPy array. It must be two-dimensional, nonempty in both
  dimensions, and contain only finite values. Negative values are allowed.
  Raise `ValueError` with `image` in the message for invalid images.
- `block_shape` contains exactly two values `(block_height, block_width)`.
  Each must be a positive integer, excluding booleans. Both dimensions of the
  image must be exactly divisible by the corresponding block dimension;
  otherwise raise `ValueError` with `block` in the message. Do not crop or pad.
- Partition the image into nonoverlapping rectangular blocks. Output cell
  `[r, c]` is the arithmetic mean of that spatial block, so the shape becomes
  `(height // block_height, width // block_width)`.
- Return a fresh float64 array, including for `(1, 1)` blocks. Never change or
  share writable memory with the input. Accept noncontiguous input views.

## Example

```python
image = np.arange(24, dtype=np.float64).reshape(4, 6)
block_means(image, (2, 3))
# array([[ 4.,  7.],
#        [16., 19.]])
```

The top-left block is `[[0, 1, 2], [6, 7, 8]]`, whose mean is 4.

## Edge cases and optional hints

Try rectangular rather than square blocks, a sliced view, one whole-image block,
unit blocks, and a nondividing block size. Name all four axes after reshaping;
reducing the wrong pair can produce plausible numbers in the wrong locations.
Tests check behavior; review your implementation manually for vectorized work.

## Run and done when

From the repository root:

```powershell
uv run pytest modules/03_data_foundations/exercises/image_pooling -q -rx
```

Edit only `starter.py`. Done when all tests pass with zero xfails and you can
explain the reshape axes and why changing the output cannot alter the input.
