"""Teacher lifecycle checks; no learner solution or quality threshold is supplied."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import pandas as pd
import pytest
from sklearn.impute import SimpleImputer
from sklearn.metrics import average_precision_score, brier_score_loss, mean_absolute_error

ROOT = Path(__file__).resolve().parents[3]
MODULE = "modules.04_machine_learning.06_reproducibility.classical_demo"


def demo() -> ModuleType:
    assert (ROOT / "modules/04_machine_learning/06_reproducibility/classical_demo.py").is_file(), (
        "Teacher lifecycle is not implemented"
    )
    return importlib.import_module(MODULE)


@pytest.mark.parametrize("scenario", ["cycling", "sensors"])
def test_partitions_cover_independent_units_and_fit_only_training_rows(
    scenario: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = demo()
    fitted_ids: list[set[str]] = []
    original = SimpleImputer.fit

    def record_fit(self: Any, x: pd.DataFrame, *args: Any, **kwargs: Any) -> Any:
        fitted_ids.append(set(x.index))
        return original(self, x, *args, **kwargs)

    monkeypatch.setattr(SimpleImputer, "fit", record_fit)
    experiment = getattr(api, f"{scenario}_experiment")(seed=31)
    parts = [set(ids) for ids in experiment.splits.values()]
    assert set.union(*parts) == set(experiment.data.index)
    assert sum(map(len, parts)) == len(experiment.data)
    assert experiment.data.index.is_unique
    assert fitted_ids
    assert all(ids == set(experiment.splits["train"]) for ids in fitted_ids)
    assert experiment.predictions.row_id.tolist() == experiment.splits["test"]


@pytest.mark.parametrize("scenario", ["cycling", "sensors"])
def test_changing_test_targets_cannot_change_selection(
    scenario: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = demo()
    original = getattr(api, f"{scenario}_experiment")(seed=31)
    source = getattr(api, f"{scenario}_data")

    def changed_data(*, seed: int) -> pd.DataFrame:
        frame: pd.DataFrame = source(seed=seed)
        # The split is frozen independently of this mutation by the injected splitter.
        frame.loc[original.splits["test"], "target"] = (
            1 - frame.loc[original.splits["test"], "target"]
            if scenario == "sensors"
            else frame.loc[original.splits["test"], "target"] + 10000
        )
        return frame

    monkeypatch.setattr(api, f"{scenario}_data", changed_data)
    monkeypatch.setattr(api, "split_rows", lambda *args, **kwargs: original.splits)
    changed = getattr(api, f"{scenario}_experiment")(seed=31)
    assert changed.report["selection"] == original.report["selection"]
    assert changed.report["development"] == original.report["development"]
    column = "probability" if scenario == "sensors" else "prediction"
    np.testing.assert_array_equal(changed.predictions[column], original.predictions[column])
    assert changed.report["test_metrics"] != original.report["test_metrics"]


def test_calibrator_only_sees_its_reserved_development_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = demo()
    seen: list[list[str]] = []
    original = api.CalibratedClassifierCV.fit

    def record(self: Any, x: pd.DataFrame, y: pd.Series, **kwargs: Any) -> Any:
        seen.append(x.index.tolist())
        return original(self, x, y, **kwargs)

    monkeypatch.setattr(api.CalibratedClassifierCV, "fit", record)
    experiment = api.sensors_experiment(seed=31)
    assert seen == [experiment.splits["calibration"]]
    assert (
        sum(experiment.report["test_metrics"]["confusion"][0])
        + sum(experiment.report["test_metrics"]["confusion"][1])
        == 32
    )


def test_export_binds_bytes_and_recomputable_metrics_without_overwriting(tmp_path: Path) -> None:
    api = demo()
    output = tmp_path / "first"
    api.run_demo(output, seed=31)
    for scenario in ("cycling", "sensors"):
        folder = output / scenario
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        rows = pd.read_csv(folder / "predictions.csv")
        source = pd.read_csv(folder / "data.csv").set_index("row_id")
        assert rows.row_id.tolist() == report["splits"]["test"]
        np.testing.assert_allclose(rows.target, source.loc[rows.row_id, "target"])
        for name, digest in report["sha256"].items():
            assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
        assert report["reloaded_predictions_equal"] is True
        assert report["versions"]["sklearn"]
        assert report["code_sha256"]
        assert report["estimator_parameters"]
        assert report["feature_units"]
        assert report["target_classes"] == ([0, 1] if scenario == "sensors" else None)
        if scenario == "cycling":
            assert report["test_metrics"]["mae_minutes"] == pytest.approx(
                mean_absolute_error(rows.target, rows.prediction)
            )
            assert sum(v["count"] for v in report["error_slices"].values()) == len(rows)
        else:
            threshold = report["selection"]["threshold"]
            np.testing.assert_array_equal(
                rows.decision, (rows.probability >= threshold).astype(int)
            )
            assert report["test_metrics"]["brier"] == pytest.approx(
                brier_score_loss(rows.target, rows.probability)
            )
            assert report["test_metrics"]["average_precision"] == pytest.approx(
                average_precision_score(rows.target, rows.probability)
            )
            assert sum(v["count"] for v in report["error_slices"].values()) == len(rows)
    before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
    with pytest.raises(FileExistsError):
        api.run_demo(output, seed=31)
    assert before == {
        p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()
    }


def test_fixed_environment_replays_and_schema_rejects_reordered_features(tmp_path: Path) -> None:
    api = demo()
    for scenario in ("cycling", "sensors"):
        first = getattr(api, f"{scenario}_experiment")(seed=31)
        second = getattr(api, f"{scenario}_experiment")(seed=31)
        assert first.report == second.report
        pd.testing.assert_frame_equal(first.predictions, second.predictions)
        x = first.data.loc[first.splits["test"], first.features]
        with pytest.raises(ValueError, match=r"feature|schema"):
            api.predict_checked(first.model, x.iloc[:, ::-1], first.features, scenario=scenario)
        with pytest.raises(ValueError, match=r"feature|schema"):
            api.predict_checked(first.model, x.assign(target=0), first.features, scenario=scenario)
        assert api.export_experiment(first, tmp_path / scenario, seed=31).is_file()


def test_figures_use_saved_validation_errors_thresholds_and_confusion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MPLBACKEND", "Agg")
    plt = pytest.importorskip("matplotlib.pyplot", reason="opt-in visualization")
    plt.switch_backend("Agg")
    api = demo()
    cycling = api.cycling_experiment(seed=31)
    sensors = api.sensors_experiment(seed=31)
    figures = api.make_figures(cycling, sensors)
    try:
        ax = figures["complexity"].axes[0]
        trees = [r for r in cycling.report["development"] if r["family"] == "tree"]
        for line, key in zip(ax.lines, ("train_mae", "validation_mae"), strict=True):
            np.testing.assert_array_equal(line.get_xdata(), [r["depth"] for r in trees])
            np.testing.assert_allclose(line.get_ydata(), [r[key] for r in trees])
        ax, matrix = figures["decisions"].axes[:2]
        trace = sensors.report["thresholds"]
        np.testing.assert_allclose(ax.lines[0].get_xdata(), [r["threshold"] for r in trace])
        np.testing.assert_array_equal(ax.lines[0].get_ydata(), [r["cost"] for r in trace])
        np.testing.assert_array_equal(
            matrix.images[0].get_array(), sensors.report["test_metrics"]["confusion"]
        )
        for figure in figures.values():
            assert all(ax.get_xlabel() and ax.get_ylabel() for ax in figure.axes)
            figure.canvas.draw()
    finally:
        for figure in figures.values():
            plt.close(figure)


def test_numeric_cli_does_not_import_plotting(tmp_path: Path) -> None:
    demo()
    code = (
        "import runpy, sys; "
        "sys.modules['matplotlib'] = None; "
        f"sys.argv = ['demo', '--output', {str(tmp_path / 'cli')!r}]; "
        f"runpy.run_module({MODULE!r}, run_name='__main__')"
    )
    result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "cli/sensors/report.json").is_file()


def test_plot_cli_exports_both_images_and_refuses_even_empty_existing_folder(
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib", reason="opt-in visualization")
    api = demo()
    api.run_demo(tmp_path / "plots", plots=True)
    for name in ("complexity", "decisions"):
        assert (tmp_path / "plots" / f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        api.run_demo(existing)
    assert not list(existing.iterdir())
