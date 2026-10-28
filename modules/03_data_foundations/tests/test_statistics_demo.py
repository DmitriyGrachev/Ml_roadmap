"""Teacher statistics experiments: calculations and real artifacts, not student credit."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import runpy
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "modules/03_data_foundations/04_practical_statistics/stats_demo.py"


def demo() -> dict[str, Any]:
    assert DEMO.is_file(), "Statistics teacher demo is not implemented"
    return runpy.run_path(str(DEMO))


def test_one_changed_observation_changes_mean_and_spread_but_not_this_median() -> None:
    api = demo()
    values = api["latency_data"]()
    np.testing.assert_array_equal(values["base"], [8, 10, 11, 14, 17])
    np.testing.assert_array_equal(values["unusual"], [8, 10, 11, 14, 300])
    summary = api["latency_comparison"]()
    np.testing.assert_allclose(summary["mean_minutes"], [12, 68.6])
    np.testing.assert_allclose(summary["median_minutes"], [11, 11])
    np.testing.assert_allclose(summary["variance_minutes2"], [10, 13390.24])
    np.testing.assert_allclose(summary["std_minutes"], [10**0.5, 115.71620456962802])


def test_conditioning_changes_denominator_without_changing_joint_count() -> None:
    api = demo()
    table = api["library_frequencies"]()
    assert table[["borrow", "no_borrow"]].values.tolist() == [[30, 10], [12, 48]]
    probabilities = api["library_probabilities"]()
    assert probabilities == pytest.approx(
        {"member": 0.4, "borrow": 0.42, "borrow_given_member": 0.75, "member_given_borrow": 5 / 7}
    )


def test_sampling_keeps_actual_draws_and_reproducible_independent_repetitions() -> None:
    api = demo()
    draws, estimates = api["sampling_experiment"](seed=7, repeats=4)
    again, repeated = api["sampling_experiment"](seed=7, repeats=4)
    other, _ = api["sampling_experiment"](seed=8, repeats=4)
    assert set(draws) == {5, 50}
    for n in (5, 50):
        assert draws[n].shape == (4, n)
        assert np.isin(draws[n], [8, 10, 11, 14, 17]).all()
        np.testing.assert_array_equal(draws[n], again[n])
        assert not np.array_equal(draws[n], other[n])
        # Read saved inputs row by row; do not require either random run to "win".
        means = [sum(row.tolist()) / n for row in draws[n]]
        np.testing.assert_allclose(estimates.loc[estimates["n"].eq(n), "mean_minutes"], means)
    pd.testing.assert_frame_equal(estimates, repeated)


@pytest.mark.parametrize(("seed", "repeats"), [(-1, 3), (0, 0), (0, -2)])
def test_sampling_rejects_invalid_experiment_size(seed: int, repeats: int) -> None:
    with pytest.raises(ValueError, match=r"seed.*repeats"):
        demo()["sampling_experiment"](seed=seed, repeats=repeats)


def test_plot_marks_match_teacher_statistics(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MPLBACKEND", "Agg")
    plt = pytest.importorskip("matplotlib.pyplot", reason="uv sync --group visualization")
    plt.switch_backend("Agg")
    api = demo()
    _, estimates = api["sampling_experiment"]()
    figures = api["make_figures"](estimates)
    try:
        comparison = figures["outlier"].axes
        np.testing.assert_array_equal(comparison[0].lines[0].get_ydata(), [8, 10, 11, 14, 17])
        np.testing.assert_array_equal(comparison[0].lines[1].get_ydata(), [8, 10, 11, 14, 300])
        np.testing.assert_allclose(
            [bar.get_height() for bar in comparison[1].patches],
            [12, 11, 10**0.5, 68.6, 11, 115.71620456962802],
        )
        for ax in figures["sampling"].axes:
            assert sum(patch.get_height() for patch in ax.patches) == 500
            np.testing.assert_array_equal(ax.lines[0].get_xdata(), [12, 12])
        for figure in figures.values():
            for ax in figure.axes:
                assert ax.get_xlabel()
                assert ax.get_ylabel()
                assert ax.get_legend() is not None
            figure.canvas.draw()
    finally:
        for figure in figures.values():
            plt.close(figure)


def test_numeric_cli_does_not_require_plotting_or_create_files(tmp_path: Path) -> None:
    demo()
    result = subprocess.run(
        [sys.executable, str(DEMO)], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert "68.6" in result.stdout
    assert not list(tmp_path.iterdir())


def test_export_preserves_fresh_inputs_and_refuses_to_overwrite(tmp_path: Path) -> None:
    if importlib.util.find_spec("matplotlib") is None:
        pytest.skip("uv sync --group visualization")
    demo()
    output = tmp_path / "statistics"
    command = [sys.executable, str(DEMO), "--output", str(output), "--seed", "7"]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    for name in ("outlier", "sampling"):
        assert (output / f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["seed"] == 7
    assert metadata["ddof"] == 0
    assert metadata["replace"] is True
    assert metadata["repeats"] == 500
    assert (
        metadata["source_sha256"]
        == hashlib.sha256((output / "latencies.csv").read_bytes()).hexdigest()
    )
    means = pd.read_csv(output / "sample_means.csv")
    for n in (5, 50):
        draws = pd.read_csv(output / f"draws_n{n}.csv").to_numpy()
        assert draws.shape == (500, n)
        np.testing.assert_allclose(means.loc[means["n"].eq(n), "mean_minutes"], draws.mean(axis=1))
    before = {file.name: file.read_bytes() for file in output.iterdir()}
    repeat = subprocess.run(command, capture_output=True, text=True)
    assert repeat.returncode != 0
    assert before == {file.name: file.read_bytes() for file in output.iterdir()}
