"""Check the fixed scalar teacher trace, never implement the student's vector update."""

from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import numpy as np
import pytest

MODULE = "modules.04_machine_learning.07_training_bridge.descent_demo"
ROOT = Path(__file__).resolve().parents[3]


def demo() -> ModuleType:
    assert (ROOT / "modules/04_machine_learning/07_training_bridge/descent_demo.py").is_file(), (
        "Descent teacher demo is not implemented"
    )
    return importlib.import_module(MODULE)


def test_trace_reuses_scalar_example_and_exposes_the_whole_chain() -> None:
    api = demo()
    trace = api.descent_trace(rate=0.05, updates=2)
    np.testing.assert_allclose(trace["coefficient"], [0.7, 1.02, 1.212])
    np.testing.assert_allclose(trace["prediction"], [1.4, 2.04, 2.424])
    np.testing.assert_allclose(trace["residual"], [-1.6, -0.96, -0.576])
    np.testing.assert_allclose(trace["loss"], [2.56, 0.9216, 0.331776])
    np.testing.assert_allclose(trace["gradient"], [-6.4, -3.84, -2.304])
    assert trace["iteration"].tolist() == [0, 1, 2]
    neighbor = importlib.import_module("modules.04_machine_learning.07_training_bridge.example")
    assert api.scalar_loss is neighbor.loss
    assert api.scalar_step is neighbor.step


def test_large_negative_gradient_steps_can_oscillate_or_increase_loss() -> None:
    api = demo()
    cycle = api.descent_trace(rate=0.25, updates=2)
    np.testing.assert_allclose(cycle["coefficient"], [0.7, 2.3, 0.7])
    np.testing.assert_allclose(cycle["loss"], [2.56, 2.56, 2.56])
    diverging = api.descent_trace(rate=0.3, updates=2)
    np.testing.assert_allclose(diverging["coefficient"], [0.7, 2.62, -0.068])
    np.testing.assert_allclose(diverging["loss"], [2.56, 5.0176, 9.834496])


def test_finite_difference_is_diagnostic_not_an_all_epsilon_guarantee() -> None:
    checks = demo().derivative_checks()
    assert checks["epsilon"].gt(0).all()
    np.testing.assert_allclose(checks["analytic"], -6.4)
    medium = checks.loc[checks["epsilon"].eq(1e-6), "numerical"].item()
    assert medium == pytest.approx(-6.4, rel=1e-8)
    np.testing.assert_allclose(
        checks["absolute_error"], np.abs(checks["numerical"] + 6.4), atol=1e-14
    )


def test_plot_values_are_the_scalar_loss_not_a_generic_training_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MPLBACKEND", "Agg")
    plt = pytest.importorskip("matplotlib.pyplot", reason="uv sync --group visualization")
    plt.switch_backend("Agg")
    api = demo()
    figure = api.make_figure()
    try:
        landscape, history = figure.axes
        x = np.asarray(landscape.lines[0].get_xdata())
        np.testing.assert_allclose(landscape.lines[0].get_ydata(), (2 * x - 3) ** 2)
        for line, rate in zip(history.lines, (0.05, 0.25, 0.3), strict=True):
            np.testing.assert_array_equal(line.get_xdata(), list(range(7)))
            np.testing.assert_allclose(line.get_ydata(), api.descent_trace(rate=rate)["loss"])
        for ax in figure.axes:
            assert ax.get_xlabel()
            assert ax.get_ylabel()
            assert ax.get_legend() is not None
        figure.canvas.draw()
    finally:
        plt.close(figure)


def test_numeric_cli_works_without_output_side_effects(tmp_path: Path) -> None:
    demo()
    command = [
        sys.executable,
        "-c",
        f"import runpy, sys; sys.path.insert(0, {str(ROOT)!r}); "
        f"runpy.run_module({MODULE!r}, run_name='__main__')",
    ]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "0.9216" in result.stdout
    assert not list(tmp_path.iterdir())


def test_export_is_reproducible_and_does_not_overwrite(tmp_path: Path) -> None:
    if importlib.util.find_spec("matplotlib") is None:
        pytest.skip("uv sync --group visualization")
    demo()
    output = tmp_path / "descent"
    command = [sys.executable, "-m", MODULE, "--output", str(output)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (output / "descent.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["rates"] == [0.05, 0.25, 0.3]
    assert metadata["updates"] == 6
    assert metadata["start"] == 0.7
    assert (output / "derivative_checks.csv").is_file()
    before = {file.name: file.read_bytes() for file in output.iterdir()}
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0
    assert before == {file.name: file.read_bytes() for file in output.iterdir()}
