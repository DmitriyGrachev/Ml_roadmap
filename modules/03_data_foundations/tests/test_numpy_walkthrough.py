"""Behavioral checks for the teacher's trace, not student mastery or memory profiling."""

from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

WALKTHROUGH = Path(__file__).parents[1] / "01_numpy" / "walkthrough.py"


def read_trace(capsys: pytest.CaptureFixture[str]) -> dict[str, str]:
    assert WALKTHROUGH.is_file(), "the runnable NumPy walkthrough is not implemented"
    namespace = runpy.run_path(str(WALKTHROUGH))
    cast(Callable[[], None], namespace["main"])()
    captured = capsys.readouterr()
    assert captured.err == ""
    return dict(line.split(": ", 1) for line in captured.out.splitlines())


def test_shape_dtype_and_selection_trace(capsys: pytest.CaptureFixture[str]) -> None:
    trace = read_trace(capsys)
    assert trace["array"] == "[[2, 4, 6], [8, 10, 12]]"
    assert trace["metadata"] == "shape=(2, 3), ndim=2, size=6, dtype=int32, itemsize=4, nbytes=24"
    assert trace["column"] == "[4, 10] shape=(2,)"
    assert trace["column_keep_axis"] == "[[4], [10]] shape=(2, 1)"
    assert trace["paired_indices"] == "[4, 12]"
    assert trace["mask_selection"] == "[8, 10, 12] shape=(3,)"
    assert trace["promotion"] == "[[2.5, 4.5, 6.5], [8.5, 10.5, 12.5]] dtype=float64"


def test_reductions_remove_the_selected_axis(capsys: pytest.CaptureFixture[str]) -> None:
    trace = read_trace(capsys)
    assert trace["axis0"] == "[10, 14, 18] shape=(3,)"
    assert trace["axis1"] == "[12, 30] shape=(2,)"
    assert trace["axis1_keepdims"] == "[[12], [30]] shape=(2, 1)"


def test_broadcast_uses_rows_and_rejects_incompatible_shapes(
    capsys: pytest.CaptureFixture[str],
) -> None:
    trace = read_trace(capsys)
    assert trace["broadcast"] == "[[True, True, False], [True, False, False]] shape=(2, 3)"
    assert trace["loop_equivalent"] == "True"
    assert trace["incompatible"] == "ValueError: (2, 3) and (2,) cannot broadcast"


def test_view_mutation_and_advanced_copy_are_not_confused(
    capsys: pytest.CaptureFixture[str],
) -> None:
    trace = read_trace(capsys)
    assert trace["sharing"] == "view=True, picked=False, copied=False"
    assert trace["after_view_write"] == "[[2, 40, 6], [8, 10, 12]]"
    assert trace["after_picked_write"] == "[[2, 40, 6], [8, 10, 12]]"
    assert trace["picked"] == "[[400, 6], [10, 12]]"
    assert trace["copied"] == "[[2, 4, 6], [8, 10, 12]]"
    assert trace["reshaped_transpose_shares"] == "False"


def test_memory_experiment_distinguishes_payload_from_new_allocation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    trace = read_trace(capsys)
    assert trace["small_payloads"] == "input=24, view=16, copied=24, mask=6, selected=12"
    assert trace["million_float64_payload"] == "8000000 bytes (no large array allocated)"
    assert trace["broadcast_view"] == "shape=(1000, 3), nbytes=12000, shares=True, writable=False"
    assert trace["offset_payload"] == "24 bytes, shares=False"
