"""CPU-only checks for the adjacent, worked example."""

from importlib import import_module

import pytest

torch = pytest.importorskip("torch", reason="Install the optional training group")
example = import_module("labs.01_pytorch_foundations.example")


def test_smoke_trains_validates_and_reloads_without_external_data(tmp_path: object) -> None:
    from pathlib import Path

    result = example.run_smoke(Path(str(tmp_path)))
    assert result["train_count"] == 19
    assert result["validation_count"] == 7
    assert result["epochs"] == 2
    assert result["checkpoint_reloaded"] is True
    assert result["prediction_count"] == 7
    assert result["task"] == "synthetic object-shape smoke"
    assert result["quality_claim"] is False
    assert Path(str(tmp_path), "shape-smoke.pt").is_file()


def test_smoke_is_reproducible_on_cpu(tmp_path: object) -> None:
    from pathlib import Path

    root = Path(str(tmp_path))
    first = example.run_smoke(root / "first")
    second = example.run_smoke(root / "second")
    assert first == second
