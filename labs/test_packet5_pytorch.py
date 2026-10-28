"""Teacher-only numerical boundaries, outside every existing student target."""

from __future__ import annotations

import importlib
import json
import math
from pathlib import Path
from typing import Any

import pytest

torch = pytest.importorskip("torch", reason="Optional training environment")


def demo() -> Any:
    # A missing walkthrough fails a test, not collection in the base environment.
    return importlib.import_module("labs.01_pytorch_foundations.walkthrough")


def test_hand_pass_matches_chain_rule_and_sgd() -> None:
    result = demo().manual_step()
    assert result["shapes"] == {
        "image": [1, 1, 4, 4],
        "flat": [1, 16],
        "hidden": [1, 8],
        "logits": [1, 2],
        "target": [1],
        "loss": [],
    }
    assert result["target_dtype"] == "torch.int64"
    assert result["input_dtype"] == "torch.float64"
    assert result["device"] == "cpu"
    assert result["preactivation"] == [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    assert result["logits"] == [[1.0, 0.0]]
    assert result["hidden"] == [[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
    assert result["loss"] == pytest.approx(0.31326168751822286, abs=1e-12)
    assert result["probabilities"][0] == pytest.approx([0.73105857863, 0.26894142137])
    assert result["gradients"] == pytest.approx(
        {
            "w1": -0.26894142137,
            "b1": -0.26894142137,
            "w20": -0.26894142137,
            "b20": -0.26894142137,
            "w21": 0.26894142137,
            "b21": 0.26894142137,
        }
    )
    assert result["finite_difference_w20"] == pytest.approx(-0.26894142137, abs=1e-8)
    assert result["accumulated_w20"] == pytest.approx(-0.53788284274)
    assert result["cleared_to_none"] is True
    assert result["after"] == pytest.approx(
        {
            "w1": 1.026894142137,
            "b1": 0.026894142137,
            "w20": 1.026894142137,
            "b20": 0.026894142137,
            "w21": -0.026894142137,
            "b21": -0.026894142137,
        }
    )
    assert result["logging_detached"] is True
    assert result["loss_after"] < result["loss"]  # This fixed smooth step, not all runs.


def test_training_trace_counts_rows_modes_and_actual_parameter_changes(tmp_path: Path) -> None:
    result = demo().run_walkthrough(tmp_path / "new")
    trace = result["training"]
    assert trace["train_batch_sizes"] == [6, 6, 6, 1]
    assert trace["validation_batch_sizes"] == [3, 3, 1]
    assert len(trace["epochs"]) == 4
    for epoch in trace["epochs"]:
        assert epoch["train_count"] == 19
        assert epoch["validation_count"] == 7
        assert all(math.isfinite(step["loss"]) for step in epoch["steps"])
        assert all(step["training"] and step["grad_enabled"] for step in epoch["steps"])
        assert all(step["gradient_norm"] > 0 for step in epoch["steps"])
        assert all(step["parameter_delta"] > 0 for step in epoch["steps"])
        expected = sum(step["loss"] * step["count"] for step in epoch["steps"]) / 19
        assert epoch["train_loss"] == pytest.approx(expected)
        losses = epoch["validation_row_losses"]
        assert len(losses) == 7
        assert epoch["validation_loss"] == pytest.approx(sum(losses) / 7)
        assert epoch["validation_modes"] == [[False, False]] * 3
        assert epoch["validation_parameter_delta"] == 0.0
    assert trace["reload_max_abs_difference"] == pytest.approx(0.0, abs=1e-7)
    assert len(trace["predictions"]) == 7
    checkpoint = torch.load(tmp_path / "new/shape-smoke.pt", weights_only=True)
    assert set(checkpoint) == {"model_state", "epoch"}  # Reuse existing inference format.
    assert checkpoint["epoch"] == 4
    assert result["quality_claim"] is False
    assert json.loads((tmp_path / "new/trace.json").read_text()) == result


def test_modes_are_separate_from_autograd() -> None:
    result = demo().mode_probe()
    assert result == {
        "eval_tracks_grad": True,
        "train_no_grad_training": True,
        "train_no_grad_tracks_grad": False,
        "eval_no_grad_tracks_grad": False,
        "eval_repeated_max_difference": 0.0,
    }


def test_demo_preserves_rng_and_repeats_same_cpu_trace(tmp_path: Path) -> None:
    before = torch.get_rng_state().clone()
    first = demo().run_walkthrough(tmp_path / "first")
    assert torch.equal(before, torch.get_rng_state())
    second = demo().run_walkthrough(tmp_path / "second")
    assert first == second


def test_existing_destination_is_never_overwritten(tmp_path: Path) -> None:
    destination = tmp_path / "old"
    destination.mkdir()
    marker = destination / "student.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        demo().run_walkthrough(destination)
    assert marker.read_text(encoding="utf-8") == "keep"
    assert list(destination.iterdir()) == [marker]


def test_plot_is_opt_in_and_saved_from_trace(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib", reason="Optional visualization environment")
    result = demo().run_walkthrough(tmp_path / "plot", plots=True)
    assert result["plots"] == ["learning.png"]
    assert (tmp_path / "plot/learning.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
