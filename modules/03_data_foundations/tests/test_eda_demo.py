"""Behavioral checks for teacher calculations and plots, not student EDA credit."""

from __future__ import annotations

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

DEMO = Path(__file__).parents[1] / "03_data_quality" / "eda_demo.py"


def demo() -> dict[str, Any]:
    assert DEMO.is_file(), "teacher EDA demonstration is not implemented"
    return runpy.run_path(str(DEMO))


def test_audit_separates_parse_failures_missing_and_invalid_without_mutation() -> None:
    api = demo()
    raw = api["ticket_sample"]()
    before = raw.copy(deep=True)
    clean, audit = api["prepare_tickets"](raw)
    assert audit == {
        "raw_rows": 12,
        "exact_duplicate_extras": 1,
        "retained_rows": 11,
        "conflicting_ticket_rows": 0,
        "missing_channel": 1,
        "missing_resolution_minutes": 1,
        "unparseable_resolution_minutes": 1,
        "invalid_resolution_minutes": 1,
        "missing_followup_minutes": 1,
        "unparseable_followup_minutes": 0,
        "invalid_followup_minutes": 0,
        "missing_opened_day": 0,
        "unparseable_opened_day": 1,
    }
    pd.testing.assert_frame_equal(raw, before)
    assert len(clean) == 11
    assert clean.loc[clean.ticket_id.eq("S-106"), "resolution_minutes"].item() == 120
    assert clean.loc[clean.ticket_id.eq("S-109"), "opened_day"].isna().all()
    assert clean.loc[clean.ticket_id.eq("S-110"), "resolution_minutes"].isna().all()
    clean.loc[0, "channel"] = "changed"
    pd.testing.assert_frame_equal(raw, before)


def test_conflicting_key_is_reported_not_arbitrarily_deleted() -> None:
    api = demo()
    raw = api["ticket_sample"]()
    conflict = raw.iloc[[0]].copy()
    conflict["resolution_minutes"] = "99"
    clean, audit = api["prepare_tickets"](pd.concat([raw, conflict], ignore_index=True))
    assert len(clean) == 12
    assert audit["conflicting_ticket_rows"] == 2


def test_each_question_uses_its_own_valid_rows_and_time_is_sorted() -> None:
    api = demo()
    clean, _ = api["prepare_tickets"](api["ticket_sample"]())
    tables = api["analysis_tables"](clean)
    assert tables["distribution"].resolution_minutes.tolist() == [8, 30, 14, 40, 120, 10, 20, 16]
    assert tables["relationship"].ticket_id.tolist() == [
        "S-101",
        "S-102",
        "S-103",
        "S-104",
        "S-106",
        "S-108",
        "S-109",
    ]
    assert tables["groups"].channel.tolist() == ["(unknown)", "chat", "email"]
    assert tables["groups"].observations.tolist() == [1, 3, 4]
    np.testing.assert_allclose(tables["groups"].mean_minutes, [20, 32 / 3, 51.5])
    assert tables["time"].opened_day.dt.strftime("%Y-%m-%d").tolist() == [
        "2026-01-01",
        "2026-01-02",
        "2026-01-03",
        "2026-01-04",
        "2026-01-05",
    ]
    assert tables["time"].observations.tolist() == [2, 2, 1, 2, 0]
    np.testing.assert_allclose(tables["time"].mean_minutes, [19, 27, 120, 15, np.nan])


def test_nonfinite_duration_is_not_plotted_and_empty_input_has_empty_tables() -> None:
    api = demo()
    raw = api["ticket_sample"]().iloc[[0]].copy()
    raw["resolution_minutes"] = "inf"
    clean, audit = api["prepare_tickets"](raw)
    assert audit["invalid_resolution_minutes"] == 1
    assert api["analysis_tables"](clean)["distribution"].empty
    empty, _ = api["prepare_tickets"](raw.iloc[:0])
    assert all(table.empty for table in api["analysis_tables"](empty).values())


def test_graph_marks_match_the_saved_calculations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MPLBACKEND", "Agg")
    plt = pytest.importorskip("matplotlib.pyplot", reason="uv sync --group visualization")
    plt.switch_backend("Agg")  # Matplotlib may have been imported before this test.
    api = demo()
    clean, _ = api["prepare_tickets"](api["ticket_sample"]())
    figures = api["make_figures"](api["analysis_tables"](clean))
    try:
        histogram = figures["distribution"].axes[0]
        assert [patch.get_height() for patch in histogram.patches] == [4, 2, 1, 0, 0, 0, 1]
        scatter = figures["relationship"].axes[0]
        np.testing.assert_allclose(
            scatter.collections[0].get_offsets(),
            [
                [8, 1],
                [30, 5],
                [14, 2],
                [40, 8],
                [120, 20],
                [20, 4],
                [16, 2],
            ],
        )
        groups = figures["groups"].axes[0]
        np.testing.assert_allclose(
            [patch.get_height() for patch in groups.patches], [20, 32 / 3, 51.5]
        )
        assert [text.get_text() for text in groups.texts] == ["n=1", "n=3", "n=4"]
        trend = figures["time"].axes[0]
        np.testing.assert_allclose(trend.lines[0].get_ydata(), [19, 27, 120, 15, np.nan])
        for figure in figures.values():
            ax = figure.axes[0]
            assert ax.get_title()
            assert ax.get_xlabel()
            assert ax.get_ylabel()
            assert "мин" in (ax.get_xlabel() + ax.get_ylabel())
            assert ax.get_legend() is not None
            figure.canvas.draw()
    finally:
        for figure in figures.values():
            plt.close(figure)


def test_cli_saves_real_images_tables_and_metadata_without_overwriting(tmp_path: Path) -> None:
    if importlib.util.find_spec("matplotlib") is None:
        pytest.skip("uv sync --group visualization")
    demo()
    output = tmp_path / "teacher-eda"
    command = [sys.executable, str(DEMO), "--output", str(output)]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    for name in ("distribution", "relationship", "groups", "time"):
        assert (output / f"{name}.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        assert (output / f"{name}.png").stat().st_size > 1000
        assert (output / f"{name}.csv").is_file()
    metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["audit"]["raw_rows"] == 12
    assert metadata["versions"]["pandas"] == pd.__version__
    assert len(metadata["source_sha256"]) == 64
    assert len(pd.read_csv(output / "raw.csv")) == 12
    assert len(pd.read_csv(output / "prepared.csv")) == 11
    original = (output / "metadata.json").read_bytes()
    repeated = subprocess.run(command, check=False, capture_output=True, text=True)
    assert repeated.returncode != 0
    assert (output / "metadata.json").read_bytes() == original


def test_plot_sample_labels_follow_a_smaller_input(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MPLBACKEND", "Agg")
    plt = pytest.importorskip("matplotlib.pyplot", reason="uv sync --group visualization")
    plt.switch_backend("Agg")
    api = demo()
    clean, _ = api["prepare_tickets"](api["ticket_sample"]().iloc[:2])
    figures = api["make_figures"](api["analysis_tables"](clean))
    try:
        assert "n=2" in figures["distribution"].axes[0].get_title()
        assert "n=2" in figures["relationship"].axes[0].get_title()
        assert figures["time"].axes[0].texts[0].get_text() == "n по дням: 2"
    finally:
        for figure in figures.values():
            plt.close(figure)
