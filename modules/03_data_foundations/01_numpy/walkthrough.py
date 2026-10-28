"""Trace small sensor arrays; no downloads, large allocations, or student solutions."""

from __future__ import annotations

import numpy as np


def main() -> None:
    """Print the states explained in theory.md, with stable list representations."""
    a = np.array([[2, 4, 6], [8, 10, 12]], dtype=np.int32)
    print(f"array: {a.tolist()}")
    print(
        f"metadata: shape={a.shape}, ndim={a.ndim}, size={a.size}, "
        f"dtype={a.dtype}, itemsize={a.itemsize}, nbytes={a.nbytes}"
    )

    column = a[:, 1]
    column_keep_axis = a[:, 1:2]
    print(f"column: {column.tolist()} shape={column.shape}")
    print(f"column_keep_axis: {column_keep_axis.tolist()} shape={column_keep_axis.shape}")
    print(f"paired_indices: {a[[0, 1], [1, 2]].tolist()}")
    mask = a > 7
    selected = a[mask]
    print(f"mask_selection: {selected.tolist()} shape={selected.shape}")
    promoted = a + 0.5
    print(f"promotion: {promoted.tolist()} dtype={promoted.dtype}")

    axis0 = a.sum(axis=0)
    axis1 = a.sum(axis=1)
    axis1_keepdims = a.sum(axis=1, keepdims=True)
    print(f"axis0: {axis0.tolist()} shape={axis0.shape}")
    print(f"axis1: {axis1.tolist()} shape={axis1.shape}")
    print(f"axis1_keepdims: {axis1_keepdims.tolist()} shape={axis1_keepdims.shape}")

    limits = np.array([5, 9], dtype=np.int32)[:, np.newaxis]
    within_limit = a <= limits
    print(f"broadcast: {within_limit.tolist()} shape={within_limit.shape}")
    loop_result = [[value <= limit for value in row] for row, limit in zip(a, [5, 9], strict=True)]
    print(f"loop_equivalent: {np.array_equal(within_limit, loop_result)}")
    try:
        a + np.array([1, 2], dtype=np.int32)
    except ValueError:
        print("incompatible: ValueError: (2, 3) and (2,) cannot broadcast")

    view = a[:, 1:]
    picked = a[:, [1, 2]]
    copied = a.copy()
    print(
        f"sharing: view={np.shares_memory(a, view)}, "
        f"picked={np.shares_memory(a, picked)}, copied={np.shares_memory(a, copied)}"
    )
    view[0, 0] = 40
    print(f"after_view_write: {a.tolist()}")
    picked[0, 0] = 400
    print(f"after_picked_write: {a.tolist()}")
    print(f"picked: {picked.tolist()}")
    print(f"copied: {copied.tolist()}")
    grid = np.arange(12, dtype=np.int32).reshape(3, 4)
    flattened = grid.T.reshape(12)
    print(f"reshaped_transpose_shares: {np.shares_memory(grid, flattened)}")

    print(
        f"small_payloads: input={a.nbytes}, view={view.nbytes}, copied={copied.nbytes}, "
        f"mask={mask.nbytes}, selected={selected.nbytes}"
    )
    estimate = 1000 * 1000 * np.dtype(np.float64).itemsize
    print(f"million_float64_payload: {estimate} bytes (no large array allocated)")
    repeated = np.broadcast_to(a[0], (1000, 3))
    print(
        f"broadcast_view: shape={repeated.shape}, nbytes={repeated.nbytes}, "
        f"shares={np.shares_memory(a, repeated)}, writable={repeated.flags.writeable}"
    )
    offset = a + 10
    print(f"offset_payload: {offset.nbytes} bytes, shares={np.shares_memory(a, offset)}")


if __name__ == "__main__":
    main()
